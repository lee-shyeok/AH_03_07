import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';

class NaverAuthService {
  static const String _clientId = 'MHBLv1HklEH4MDoNoHYF';
  static const String _redirectUri = 'http://localhost:8080/naver-callback';

  static String _generateState() {
    final random = Random.secure();
    return List.generate(16, (_) => random.nextInt(16).toRadixString(16)).join();
  }

  static Future<Map<String, dynamic>?> signIn(BuildContext context) async {
    final state = _generateState();
    final authUrl = Uri.parse(
      'https://nid.naver.com/oauth2.0/authorize'
      '?response_type=code'
      '&client_id=$_clientId'
      '&redirect_uri=${Uri.encodeComponent(_redirectUri)}'
      '&state=$state',
    );

    // 네이버 로그인 다이얼로그
    final result = await showDialog<Map<String, String>>(
      context: context,
      barrierDismissible: false,
      builder: (_) => NaverLoginDialog(
        authUrl: authUrl.toString(),
        redirectUri: _redirectUri,
        state: state,
      ),
    );

    if (result == null) return null;

    final code = result['code'];
    final returnedState = result['state'];

    if (code == null || returnedState != state) {
      throw Exception('네이버 로그인 인증에 실패했습니다.');
    }

    final response = await http.post(
      Uri.parse('${OcrConfig.baseUrl}/v1/auth/naver'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'code': code, 'state': returnedState}),
    ).timeout(OcrConfig.timeoutDuration);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      final error = jsonDecode(response.body);
      throw Exception(error['detail'] ?? '네이버 로그인에 실패했습니다.');
    }
  }
}

class NaverLoginDialog extends StatefulWidget {
  final String authUrl;
  final String redirectUri;
  final String state;

  const NaverLoginDialog({
    super.key,
    required this.authUrl,
    required this.redirectUri,
    required this.state,
  });

  @override
  State<NaverLoginDialog> createState() => _NaverLoginDialogState();
}

class _NaverLoginDialogState extends State<NaverLoginDialog> {
  final _codeController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  void _openNaverLogin() async {
    // 웹에서는 새 탭으로 열기
    // ignore: avoid_web_libraries_in_flutter
    // dart:html 대신 url_launcher 사용
    _showManualInput();
  }

  void _showManualInput() {
    // 웹뷰 대신 URL 안내 + 코드 입력 방식
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('네이버 로그인'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('아래 URL을 복사해서 브라우저에서 열고\n로그인 후 리다이렉트된 URL의\ncode 값을 입력하세요.'),
            const SizedBox(height: 12),
            SelectableText(
              widget.authUrl,
              style: const TextStyle(fontSize: 11, color: Colors.blue),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _codeController,
              decoration: const InputDecoration(
                labelText: 'code 값 입력',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () {
              final code = _codeController.text.trim();
              if (code.isNotEmpty) {
                Navigator.pop(ctx);
                Navigator.pop(context, {'code': code, 'state': widget.state});
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF03C75A)),
            child: const Text('확인', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: Row(
        children: [
          Container(
            width: 28, height: 28,
            decoration: BoxDecoration(
              color: const Color(0xFF03C75A),
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Center(
              child: Text('N', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
          ),
          const SizedBox(width: 8),
          const Text('네이버로 로그인'),
        ],
      ),
      content: const Text('네이버 로그인 페이지로 이동합니다.'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('취소'),
        ),
        ElevatedButton(
          onPressed: _openNaverLogin,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF03C75A),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          child: const Text('로그인하기', style: TextStyle(color: Colors.white)),
        ),
      ],
    );
  }
}