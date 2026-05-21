import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'services/ocr_service.dart';
import 'services/auth_service.dart';
import 'main.dart';

enum SignupStep { emailVerify, infoInput }

class SignupPage extends StatefulWidget {
  final VoidCallback onSignupSuccess;
  const SignupPage({super.key, required this.onSignupSuccess});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  SignupStep _step = SignupStep.emailVerify;

  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  String? _emailToken;
  bool _codeSent = false;
  int _resendCooldown = 0;

  final _formKey = GlobalKey<FormState>();
  final _passwordController = TextEditingController();
  final _passwordConfirmController = TextEditingController();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  DateTime? _birthDate;
  String? _gender;
  bool _agreedAll = false;
  bool _agreedTerms = false;
  bool _agreedPrivacy = false;
  bool _agreedSensitive = false;

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscurePasswordConfirm = true;
  String _errorMessage = '';

  late final SecureTokenStorage _tokenStorage;
  late final AuthService _authService;

  static final _emailRegex = RegExp(r'^[\w.-]+@[\w.-]+\.\w{2,}$');
  static final _phoneRegex = RegExp(r'^01[0-9]{8,9}$');
  static final _passwordRegex =
      RegExp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$');

  @override
  void initState() {
    super.initState();
    _tokenStorage = SecureTokenStorage();
    _authService = AuthService(tokenStorage: _tokenStorage);
  }

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _passwordConfirmController.dispose();
    _nameController.dispose();
    _phoneController.dispose();
    _authService.dispose();
    super.dispose();
  }

  void _startResendTimer() {
    setState(() => _resendCooldown = 60);
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (!mounted) return false;
      setState(() => _resendCooldown--);
      return _resendCooldown > 0;
    });
  }

  Future<void> _sendCode() async {
    final email = _emailController.text.trim();
    if (email.isEmpty) {
      setState(() => _errorMessage = '이메일을 입력해주세요.');
      return;
    }
    if (!_emailRegex.hasMatch(email)) {
      setState(() => _errorMessage = '올바른 이메일 형식이 아닙니다.');
      return;
    }
    if (_resendCooldown > 0) return;

    setState(() { _isLoading = true; _errorMessage = ''; });

    try {
      final response = await http.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/email-verify/send'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email}),
      ).timeout(OcrConfig.timeoutDuration);

      if (response.statusCode == 200) {
        setState(() => _codeSent = true);
        _startResendTimer();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('인증코드가 발송됐습니다.')),
          );
        }
      } else {
        final json = _parseBody(response.body);
        setState(() => _errorMessage = _extractMessage(json));
      }
    } on http.ClientException {
      setState(() => _errorMessage = '네트워크 오류가 발생했습니다.');
    } on TimeoutException {
      setState(() => _errorMessage = '요청 시간이 초과됐습니다.');
    } catch (_) {
      setState(() => _errorMessage = '알 수 없는 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _verifyCode() async {
    final email = _emailController.text.trim();
    final code = _codeController.text.trim();

    if (code.length != 6) {
      setState(() => _errorMessage = '6자리 인증코드를 입력해주세요.');
      return;
    }

    setState(() { _isLoading = true; _errorMessage = ''; });

    try {
      final response = await http.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/email-verify/confirm'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'code': code}),
      ).timeout(OcrConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final json = _parseBody(response.body);
        if (mounted) {
          setState(() {
            _emailToken = json['email_token'] as String;
            _step = SignupStep.infoInput;
          });
        }
      } else {
        final json = _parseBody(response.body);
        setState(() => _errorMessage = _extractMessage(json));
      }
    } on http.ClientException {
      setState(() => _errorMessage = '네트워크 오류가 발생했습니다.');
    } on TimeoutException {
      setState(() => _errorMessage = '요청 시간이 초과됐습니다.');
    } catch (_) {
      setState(() => _errorMessage = '알 수 없는 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signup() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (!_agreedTerms || !_agreedPrivacy || !_agreedSensitive) {
      setState(() => _errorMessage = '모든 약관에 동의해주세요.');
      return;
    }

    FocusScope.of(context).unfocus();
    setState(() { _isLoading = true; _errorMessage = ''; });

    try {
      final response = await http.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': _emailController.text.trim(),
          'email_token': _emailToken,
          'password': _passwordController.text,
          'password_confirm': _passwordConfirmController.text,
          'name': _nameController.text.trim(),
          'birth_date': '${_birthDate!.year}-'
              '${_birthDate!.month.toString().padLeft(2, '0')}-'
              '${_birthDate!.day.toString().padLeft(2, '0')}',
          'gender': _gender,
          'phone_number': _phoneController.text.trim(),
          'agreed_terms': _agreedTerms,
          'agreed_privacy': _agreedPrivacy,
          'agreed_sensitive_medical': _agreedSensitive,
        }),
      ).timeout(OcrConfig.timeoutDuration);

      if (response.statusCode == 201) {
        final json = _parseBody(response.body);
        await _tokenStorage.saveAccessToken(json['access_token'] as String);
        await _tokenStorage.saveRefreshToken(json['refresh_token'] as String);
        if (mounted) widget.onSignupSuccess();
      } else {
        final json = _parseBody(response.body);
        setState(() => _errorMessage = _extractMessage(json));
      }
    } on http.ClientException {
      setState(() => _errorMessage = '네트워크 오류가 발생했습니다.');
    } on TimeoutException {
      setState(() => _errorMessage = '요청 시간이 초과됐습니다.');
    } catch (_) {
      setState(() => _errorMessage = '알 수 없는 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Map<String, dynamic> _parseBody(String body) {
    try {
      return jsonDecode(body) as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }

  String _extractMessage(Map<String, dynamic> json) {
    final detail = json['detail'];
    if (detail is String) return detail;
    if (detail is Map) return (detail['message'] as String?) ?? '오류가 발생했습니다.';
    return '오류가 발생했습니다.';
  }

  Future<void> _pickBirthDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(2000),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
      locale: const Locale('ko', 'KR'),
    );
    if (picked != null && mounted) setState(() => _birthDate = picked);
  }

  void _setAgreedAll(bool? value) {
    setState(() {
      _agreedAll = value ?? false;
      _agreedTerms = _agreedAll;
      _agreedPrivacy = _agreedAll;
      _agreedSensitive = _agreedAll;
    });
  }

  void _updateAgreedAll() {
    setState(() {
      _agreedAll = _agreedTerms && _agreedPrivacy && _agreedSensitive;
    });
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !_isLoading,
      child: Scaffold(
        appBar: AppBar(
          title: Text(_step == SignupStep.emailVerify ? '이메일 인증' : '회원가입'),
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: _step == SignupStep.emailVerify
                ? _buildEmailStep()
                : _buildInfoStep(),
          ),
        ),
      ),
    );
  }

  Widget _buildEmailStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 20),
        TextField(
          controller: _emailController,
          decoration: const InputDecoration(
            labelText: '이메일',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.email_outlined),
          ),
          keyboardType: TextInputType.emailAddress,
          enabled: !_isLoading && !_codeSent,
        ),
        const SizedBox(height: 12),
        ElevatedButton(
          onPressed: (_isLoading || _resendCooldown > 0) ? null : _sendCode,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFFF8C00),
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: Text(
            _resendCooldown > 0
                ? '재발송 ($_resendCooldown초)'
                : (_codeSent ? '재발송' : '인증코드 발송'),
            style: const TextStyle(color: Colors.white),
          ),
        ),
        if (_codeSent) ...[
          const SizedBox(height: 16),
          TextField(
            controller: _codeController,
            decoration: const InputDecoration(
              labelText: '인증코드 6자리',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.lock_outline),
            ),
            keyboardType: TextInputType.number,
            maxLength: 6,
            enabled: !_isLoading,
          ),
          ElevatedButton(
            onPressed: _isLoading ? null : _verifyCode,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF8C00),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: _isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                        color: Colors.white, strokeWidth: 2),
                  )
                : const Text('인증 확인',
                    style: TextStyle(color: Colors.white)),
          ),
        ],
        if (_errorMessage.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(_errorMessage, style: const TextStyle(color: Colors.red)),
        ],
      ],
    );
  }

  Widget _buildInfoStep() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 20),
          TextFormField(
            controller: _passwordController,
            decoration: InputDecoration(
              labelText: '비밀번호',
              border: const OutlineInputBorder(),
              prefixIcon: const Icon(Icons.lock_outlined),
              suffixIcon: IconButton(
                icon: Icon(_obscurePassword
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined),
                onPressed: () =>
                    setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),
            obscureText: _obscurePassword,
            validator: (v) {
              if (v == null || v.isEmpty) return '비밀번호를 입력해주세요.';
              if (!_passwordRegex.hasMatch(v)) return '영문, 숫자, 특수문자 포함 8자 이상';
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordConfirmController,
            decoration: InputDecoration(
              labelText: '비밀번호 확인',
              border: const OutlineInputBorder(),
              prefixIcon: const Icon(Icons.lock_outlined),
              suffixIcon: IconButton(
                icon: Icon(_obscurePasswordConfirm
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined),
                onPressed: () => setState(
                    () => _obscurePasswordConfirm = !_obscurePasswordConfirm),
              ),
            ),
            obscureText: _obscurePasswordConfirm,
            validator: (v) {
              if (v != _passwordController.text) return '비밀번호가 일치하지 않습니다.';
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _nameController,
            decoration: const InputDecoration(
              labelText: '이름',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.person_outlined),
            ),
            validator: (v) =>
                v == null || v.trim().isEmpty ? '이름을 입력해주세요.' : null,
          ),
          const SizedBox(height: 16),

          // 생년월일
          FormField<DateTime>(
            validator: (_) =>
                _birthDate == null ? '생년월일을 선택해주세요.' : null,
            builder: (field) => GestureDetector(
              onTap: _pickBirthDate,
              child: AbsorbPointer(
                child: TextFormField(
                  controller: TextEditingController(
                    text: _birthDate == null
                        ? ''
                        : '${_birthDate!.year}년 '
                            '${_birthDate!.month}월 '
                            '${_birthDate!.day}일',
                  ),
                  decoration: InputDecoration(
                    labelText: '생년월일',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.calendar_today_outlined),
                    hintText: '선택해주세요',
                    errorText: field.errorText,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),

          DropdownButtonFormField<String>(
            value: _gender,
            decoration: const InputDecoration(
              labelText: '성별',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.person_outline),
            ),
            items: const [
              DropdownMenuItem(value: 'male', child: Text('남성')),
              DropdownMenuItem(value: 'female', child: Text('여성')),
              DropdownMenuItem(value: 'other', child: Text('기타')),
            ],
            onChanged: (v) => setState(() => _gender = v),
            validator: (v) => v == null ? '성별을 선택해주세요.' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _phoneController,
            decoration: const InputDecoration(
              labelText: '휴대폰 번호',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.phone_outlined),
              hintText: '01012345678',
            ),
            keyboardType: TextInputType.phone,
            validator: (v) {
              if (v == null || v.isEmpty) return '휴대폰 번호를 입력해주세요.';
              if (!_phoneRegex.hasMatch(v)) return '올바른 형식: 01012345678';
              return null;
            },
          ),
          const SizedBox(height: 24),
          CheckboxListTile(
            value: _agreedAll,
            onChanged: _setAgreedAll,
            title: const Text('전체 동의',
                style: TextStyle(fontWeight: FontWeight.bold)),
            controlAffinity: ListTileControlAffinity.leading,
          ),
          const Divider(),
          _buildCheckbox('서비스 이용약관 동의 (필수)', _agreedTerms, (v) {
            setState(() => _agreedTerms = v ?? false);
            _updateAgreedAll();
          }),
          _buildCheckbox('개인정보 처리방침 동의 (필수)', _agreedPrivacy, (v) {
            setState(() => _agreedPrivacy = v ?? false);
            _updateAgreedAll();
          }),
          _buildCheckbox('민감 의료정보 처리 동의 (필수)', _agreedSensitive, (v) {
            setState(() => _agreedSensitive = v ?? false);
            _updateAgreedAll();
          }),
          const SizedBox(height: 16),
          if (_errorMessage.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_errorMessage,
                  style: const TextStyle(color: Colors.red)),
            ),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _signup,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF8C00),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 0,
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2),
                    )
                  : const Text('회원가입',
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckbox(String label, bool value, Function(bool?) onChanged) {
    return CheckboxListTile(
      value: value,
      onChanged: onChanged,
      title: Text(label, style: const TextStyle(fontSize: 13)),
      controlAffinity: ListTileControlAffinity.leading,
      dense: true,
    );
  }
}