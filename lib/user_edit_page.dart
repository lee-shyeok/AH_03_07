import 'package:flutter/material.dart';
import 'services/user_service.dart';
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';
import 'chip_section.dart';

class UserEditPage extends StatefulWidget {
  final TokenStorage tokenStorage;
  final UserProfile profile;
  final VoidCallback? onWithdraw;

  const UserEditPage({
    super.key,
    required this.tokenStorage,
    required this.profile,
    this.onWithdraw,
  });

  @override
  State<UserEditPage> createState() => _UserEditPageState();
}

class _UserEditPageState extends State<UserEditPage> {
  late final UserService _userService;

  late final TextEditingController _nameController;
  late final TextEditingController _heightController;
  late final TextEditingController _weightController;
  bool _savingProfile = false;

  late final TextEditingController _phoneController;
  bool _savingPhone = false;

  final _currentPwController = TextEditingController();
  final _newPwController = TextEditingController();
  final _confirmPwController = TextEditingController();
  bool _obscureCurrent = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  bool _savingPw = false;

  static final _passwordRegex =
      RegExp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$');
  static final _phoneRegex = RegExp(r'^01[0-9]{8,9}$');

  static const _green = Color(0xFF2ECC71);
  static const _bg = Color(0xFFF8FAF8);
  static const _cardBg = Colors.white;
  static const _textPrimary = Color(0xFF1A1A1A);
  static const _textSecondary = Color(0xFF888888);

  @override
  void initState() {
    super.initState();
    _userService = UserService(tokenStorage: widget.tokenStorage);
    _nameController = TextEditingController(text: widget.profile.name);
    _heightController = TextEditingController(
      text: widget.profile.height?.toStringAsFixed(0) ?? '',
    );
    _weightController = TextEditingController(
      text: widget.profile.weight?.toStringAsFixed(0) ?? '',
    );
    _phoneController =
        TextEditingController(text: widget.profile.phone ?? '');
  }

  @override
  void dispose() {
    _userService.dispose();
    _nameController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    _phoneController.dispose();
    _currentPwController.dispose();
    _newPwController.dispose();
    _confirmPwController.dispose();
    super.dispose();
  }

  void _showSnack(String msg, {bool isError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: isError ? Colors.red : _green,
    ));
  }

  Future<void> _saveProfile() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      _showSnack('이름을 입력해주세요.', isError: true);
      return;
    }
    setState(() => _savingProfile = true);
    try {
      await _userService.patchMe({
        'name': name,
        if (_heightController.text.trim().isNotEmpty)
          'height': double.tryParse(_heightController.text.trim()),
        if (_weightController.text.trim().isNotEmpty)
          'weight': double.tryParse(_weightController.text.trim()),
      });
      _showSnack('프로필이 저장됐습니다.');
    } on AuthException catch (e) {
      _showSnack(e.message, isError: true);
    } catch (_) {
      _showSnack('저장 중 오류가 발생했습니다.', isError: true);
    } finally {
      if (mounted) setState(() => _savingProfile = false);
    }
  }

  Future<void> _savePhone() async {
    final phone = _phoneController.text.trim();
    if (!_phoneRegex.hasMatch(phone)) {
      _showSnack('올바른 형식: 01012345678', isError: true);
      return;
    }
    setState(() => _savingPhone = true);
    try {
      await _userService.patchMe({'phone_number': phone});
      _showSnack('휴대폰 번호가 저장됐습니다.');
    } on AuthException catch (e) {
      _showSnack(e.message, isError: true);
    } catch (_) {
      _showSnack('저장 중 오류가 발생했습니다.', isError: true);
    } finally {
      if (mounted) setState(() => _savingPhone = false);
    }
  }

  Future<void> _savePassword() async {
    final current = _currentPwController.text;
    final newPw = _newPwController.text;
    final confirm = _confirmPwController.text;
    if (current.isEmpty) {
      _showSnack('현재 비밀번호를 입력해주세요.', isError: true);
      return;
    }
    if (!_passwordRegex.hasMatch(newPw)) {
      _showSnack('영문, 숫자, 특수문자 포함 8자 이상', isError: true);
      return;
    }
    if (newPw != confirm) {
      _showSnack('새 비밀번호가 일치하지 않습니다.', isError: true);
      return;
    }
    setState(() => _savingPw = true);
    try {
      await _userService.patchMe({
        'current_password': current,
        'new_password': newPw,
        'new_password_confirm': confirm,
      });
      _currentPwController.clear();
      _newPwController.clear();
      _confirmPwController.clear();
      _showSnack('비밀번호가 변경됐습니다.');
    } on AuthException catch (e) {
      _showSnack(e.message, isError: true);
    } catch (_) {
      _showSnack('저장 중 오류가 발생했습니다.', isError: true);
    } finally {
      if (mounted) setState(() => _savingPw = false);
    }
  }

  void _confirmWithdraw() {
    final pwController = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('회원탈퇴',
            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('탈퇴 시 모든 데이터가 삭제되며\n복구할 수 없습니다.',
                style: TextStyle(fontSize: 14)),
            const SizedBox(height: 16),
            TextField(
              controller: pwController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: '비밀번호 확인',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.lock_outline),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: _textSecondary)),
          ),
          TextButton(
            onPressed: () async {
              final pw = pwController.text;
              Navigator.pop(ctx);
              await _withdraw(pw);
            },
            child: const Text('탈퇴하기',
                style: TextStyle(
                    color: Colors.red, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Future<void> _withdraw(String password) async {
    if (password.isEmpty) {
      _showSnack('비밀번호를 입력해주세요.', isError: true);
      return;
    }
    try {
      await _userService.deleteMe(password);
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(
            builder: (_) => LoginPage(onLoginSuccess: () {})),
        (route) => false,
      );
    } on AuthException catch (e) {
      _showSnack(e.message, isError: true);
    } catch (_) {
      _showSnack('탈퇴 중 오류가 발생했습니다.', isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        leading: IconButton(
          icon:
              const Icon(Icons.chevron_left, color: _textPrimary, size: 28),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('내 정보 수정',
            style: TextStyle(
                color: _textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w600)),
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionLabel('프로필'),
            const SizedBox(height: 8),
            _buildCard([
              _buildField('이름', _nameController, hint: '홍길동'),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(
                    child: _buildField('키 (cm)', _heightController,
                        hint: '170',
                        keyboardType: TextInputType.number)),
                const SizedBox(width: 12),
                Expanded(
                    child: _buildField('몸무게 (kg)', _weightController,
                        hint: '65',
                        keyboardType: TextInputType.number)),
              ]),
              const SizedBox(height: 16),
              _saveButton('저장', _savingProfile, _saveProfile),
            ]),
            const SizedBox(height: 20),

            _sectionLabel('휴대폰 번호'),
            const SizedBox(height: 8),
            _buildCard([
              _buildField('휴대폰 번호', _phoneController,
                  hint: '01012345678',
                  keyboardType: TextInputType.phone),
              const SizedBox(height: 16),
              _saveButton('저장', _savingPhone, _savePhone),
            ]),
            const SizedBox(height: 20),

            _sectionLabel('비밀번호 변경'),
            const SizedBox(height: 8),
            _buildCard([
              _buildPasswordField('현재 비밀번호', _currentPwController,
                  obscure: _obscureCurrent,
                  onToggle: () => setState(
                      () => _obscureCurrent = !_obscureCurrent)),
              const SizedBox(height: 12),
              _buildPasswordField('새 비밀번호', _newPwController,
                  obscure: _obscureNew,
                  onToggle: () =>
                      setState(() => _obscureNew = !_obscureNew)),
              const SizedBox(height: 4),
              const Text('영문, 숫자, 특수문자 포함 8자 이상',
                  style: TextStyle(fontSize: 12, color: _textSecondary)),
              const SizedBox(height: 12),
              _buildPasswordField('새 비밀번호 확인', _confirmPwController,
                  obscure: _obscureConfirm,
                  onToggle: () => setState(
                      () => _obscureConfirm = !_obscureConfirm)),
              const SizedBox(height: 16),
              _saveButton('변경', _savingPw, _savePassword),
            ]),
            const SizedBox(height: 20),

            _sectionLabel('만성질환'),
            const SizedBox(height: 8),
            ChipSection(
              tokenStorage: widget.tokenStorage,
              initialItems: widget.profile.chronicDiseases,
              hint: '예: 당뇨, 고혈압',
              saveKey: 'chronic_diseases',
            ),
            const SizedBox(height: 20),

            _sectionLabel('알레르기'),
            const SizedBox(height: 8),
            ChipSection(
              tokenStorage: widget.tokenStorage,
              initialItems: widget.profile.allergies,
              hint: '예: 페니실린, 아스피린',
              saveKey: 'allergy_info',
            ),
            const SizedBox(height: 32),

            Center(
              child: TextButton(
                onPressed: _confirmWithdraw,
                child: const Text('회원탈퇴',
                    style: TextStyle(
                        color: Colors.red,
                        fontSize: 14,
                        decoration: TextDecoration.underline)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionLabel(String text) => Text(text,
      style: const TextStyle(
          fontSize: 13,
          color: _textSecondary,
          fontWeight: FontWeight.w500));

  Widget _buildCard(List<Widget> children) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: _cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFE8E8E8)),
        ),
        child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: children),
      );

  Widget _buildField(String label, TextEditingController controller,
          {String? hint,
          TextInputType keyboardType = TextInputType.text}) =>
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label,
            style:
                const TextStyle(fontSize: 13, color: _textSecondary)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          decoration: InputDecoration(
            hintText: hint,
            border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10)),
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 14, vertical: 12),
          ),
        ),
      ]);

  Widget _buildPasswordField(String label, TextEditingController controller,
          {required bool obscure, required VoidCallback onToggle}) =>
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label,
            style:
                const TextStyle(fontSize: 13, color: _textSecondary)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          obscureText: obscure,
          decoration: InputDecoration(
            border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10)),
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 14, vertical: 12),
            suffixIcon: IconButton(
              icon: Icon(
                  obscure
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                  size: 20),
              onPressed: onToggle,
            ),
          ),
        ),
      ]);

  Widget _saveButton(
          String label, bool saving, Future<void> Function() onPressed) =>
      SizedBox(
        width: double.infinity,
        height: 46,
        child: ElevatedButton(
          onPressed: saving ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: _green,
            disabledBackgroundColor: _green.withOpacity(0.5),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
            elevation: 0,
          ),
          child: saving
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                      color: Colors.white, strokeWidth: 2.5))
              : Text(label,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w700)),
        ),
      );
}