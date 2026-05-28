import 'package:flutter/material.dart';
import 'services/auth_service.dart';
import 'services/google_auth_service.dart';
import 'services/naver_auth_service.dart';
import 'main.dart';
import 'signup_page.dart';
import 'home_page.dart';
import 'services/ocr_service.dart';
class LoginPage extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginPage({super.key, required this.onLoginSuccess});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  late final AuthService _authService;

  bool _isLoading = false;
  bool _isGoogleLoading = false;
  bool _isNaverLoading = false;
  bool _obscurePassword = true;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _authService = AuthService(tokenStorage: SecureTokenStorage());
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    _authService.dispose();
    super.dispose();
  }

  bool get _isAnyLoading => _isLoading || _isGoogleLoading || _isNaverLoading;

  String? _validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) return '이메일을 입력해주세요.';
    final regex = RegExp(r'^[\w.-]+@[\w.-]+\.\w{2,}$');
    if (!regex.hasMatch(value.trim())) return '올바른 이메일 형식이 아닙니다.';
    return null;
  }

  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) return '비밀번호를 입력해주세요.';
    if (value.length < 8) return '비밀번호는 8자 이상이어야 합니다.';
    return null;
  }

  Future<void> _login() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    FocusScope.of(context).unfocus();
    setState(() { _isLoading = true; _errorMessage = ''; });
    try {
      await _authService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );
      if (mounted) _goHome();
    } on AuthException catch (e) {
      if (mounted) setState(() => _errorMessage = e.message);
    } catch (_) {
      if (mounted) setState(() => _errorMessage = '알 수 없는 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _googleLogin() async {
    setState(() { _isGoogleLoading = true; _errorMessage = ''; });
    try {
      final result = await GoogleAuthService.signIn();
      if (result == null) return;
      final storage = SecureTokenStorage();
      await storage.saveAccessToken(result['access_token'] as String);
      await storage.saveRefreshToken(result['refresh_token'] as String);
      if (mounted) _goHome();
    } catch (e) {
      if (mounted) setState(() => _errorMessage = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isGoogleLoading = false);
    }
  }

  Future<void> _naverLogin() async {
    setState(() { _isNaverLoading = true; _errorMessage = ''; });
    try {
      final result = await NaverAuthService.signIn(context);
      if (result == null) return;
      final storage = SecureTokenStorage();
      await storage.saveAccessToken(result['access_token'] as String);
      await storage.saveRefreshToken(result['refresh_token'] as String);
      if (mounted) _goHome();
    } catch (e) {
      if (mounted) setState(() => _errorMessage = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isNaverLoading = false);
    }
  }

  void _goHome() {
    Navigator.of(context).pushAndRemoveUntil(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => const HomePage(),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
        transitionDuration: const Duration(milliseconds: 400),
      ),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 48),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 40),
                const Text('반가워요!',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.black87)),
                const SizedBox(height: 8),
                const Text('로그인이 필요해요',
                    style: TextStyle(fontSize: 15, color: Colors.grey)),
                const SizedBox(height: 48),

                // 이메일
                TextFormField(
                  controller: _emailController,
                  focusNode: _emailFocusNode,
                  decoration: const InputDecoration(
                    labelText: '이메일',
                    hintText: 'example@email.com',
                    border: UnderlineInputBorder(),
                    enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                    focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: Color(0xFFFF8C00))),
                    labelStyle: TextStyle(color: Colors.grey),
                  ),
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  onFieldSubmitted: (_) => FocusScope.of(context).requestFocus(_passwordFocusNode),
                  validator: _validateEmail,
                  enabled: !_isAnyLoading,
                ),
                const SizedBox(height: 24),

                // 비밀번호
                TextFormField(
                  controller: _passwordController,
                  focusNode: _passwordFocusNode,
                  decoration: InputDecoration(
                    labelText: '비밀번호',
                    border: const UnderlineInputBorder(),
                    enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                    focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Color(0xFFFF8C00))),
                    labelStyle: const TextStyle(color: Colors.grey),
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined, color: Colors.grey),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  obscureText: _obscurePassword,
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _isAnyLoading ? null : _login(),
                  validator: _validatePassword,
                  enabled: !_isAnyLoading,
                ),
                const SizedBox(height: 16),

                if (_errorMessage.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(_errorMessage, style: const TextStyle(color: Colors.red, fontSize: 13)),
                  ),
                const SizedBox(height: 32),

                // 로그인 버튼
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isAnyLoading ? null : _login,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFFF8C00),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                    child: _isLoading
                        ? const SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Text('로그인', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 16),

                // 구분선
                Row(children: [
                  Expanded(child: Divider(color: Colors.grey.shade300)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text('또는', style: TextStyle(color: Colors.grey.shade500, fontSize: 13)),
                  ),
                  Expanded(child: Divider(color: Colors.grey.shade300)),
                ]),
                const SizedBox(height: 16),

                // 구글 로그인 버튼
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: OutlinedButton(
                    onPressed: _isAnyLoading ? null : _googleLogin,
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: Colors.grey.shade300),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _isGoogleLoading
                        ? const SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(color: Color(0xFFFF8C00), strokeWidth: 2))
                        : Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Image.network(
                                'https://www.google.com/favicon.ico',
                                width: 20, height: 20,
                                errorBuilder: (_, __, ___) => const Icon(Icons.g_mobiledata, color: Color(0xFF4285F4), size: 24),
                              ),
                              const SizedBox(width: 10),
                              const Text('Google로 계속하기',
                                  style: TextStyle(color: Colors.black87, fontSize: 15, fontWeight: FontWeight.w500)),
                            ],
                          ),
                  ),
                ),
                const SizedBox(height: 12),

                // 네이버 로그인 버튼
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isAnyLoading ? null : _naverLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF03C75A),
                      disabledBackgroundColor: Colors.grey.shade300,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                    child: _isNaverLoading
                        ? const SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                width: 20, height: 20,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Center(
                                  child: Text('N', style: TextStyle(
                                    color: Color(0xFF03C75A),
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                  )),
                                ),
                              ),
                              const SizedBox(width: 10),
                              const Text('네이버로 계속하기',
                                  style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                            ],
                          ),
                  ),
                ),
                const SizedBox(height: 24),

                // 이메일 찾기 / 회원가입
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    TextButton(
                      onPressed: () {},
                      child: const Text('이메일 찾기', style: TextStyle(color: Colors.grey, fontSize: 13)),
                    ),
                    const Text('|', style: TextStyle(color: Colors.grey)),
                    TextButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => SignupPage(
                              onSignupSuccess: () {
                                Navigator.pop(context);
                                widget.onLoginSuccess();
                              },
                            ),
                          ),
                        );
                      },
                      child: const Text('회원가입', style: TextStyle(color: Colors.grey, fontSize: 13)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}