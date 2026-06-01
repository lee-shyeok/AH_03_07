import 'dart:convert';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';

class GoogleAuthService {
  static bool _initialized = false;

  static Future<void> _ensureInitialized() async {
    if (_initialized) return;
    await GoogleSignIn.instance.initialize(
      clientId: '225363408316-tc94smckivafff92d7tunfjd07g7fmn6.apps.googleusercontent.com',
    );
    _initialized = true;
  }

  static Future<Map<String, dynamic>?> signIn() async {
    await _ensureInitialized();
    await GoogleSignIn.instance.signOut();

    // v7: authenticate()는 GoogleSignInAccount를 반환
    final account = await GoogleSignIn.instance.authenticate();

    final idToken = account.authentication.idToken;
    if (idToken == null) throw Exception('구글 ID 토큰을 가져올 수 없습니다.');

    final response = await http.post(
      Uri.parse('${OcrConfig.baseUrl}/v1/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'id_token': idToken}),
    ).timeout(OcrConfig.timeoutDuration);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    final error = jsonDecode(response.body) as Map<String, dynamic>;
    throw Exception(error['detail'] ?? '구글 로그인에 실패했습니다.');
  }

  static Future<void> signOut() async {
    await _ensureInitialized();
    await GoogleSignIn.instance.signOut();
  }
}
