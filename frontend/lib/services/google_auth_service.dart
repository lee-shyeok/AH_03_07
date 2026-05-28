import 'dart:convert';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';

class GoogleAuthService {
  static final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: '225363408316-tc94smckivafff92d7tunfjd07g7fmn6.apps.googleusercontent.com',
    scopes: ['email', 'profile'],
  );

  static Future<Map<String, dynamic>?> signIn() async {
    try {
      await _googleSignIn.signOut();

      final GoogleSignInAccount? account = await _googleSignIn.signIn();
      if (account == null) return null;

      final GoogleSignInAuthentication auth = await account.authentication;

      final String? idToken = auth.idToken;
      final String? accessToken = auth.accessToken;

      final String? token = idToken ?? accessToken;
      if (token == null) {
        throw Exception('구글 토큰을 가져올 수 없습니다.');
      }

      final response = await http.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/google'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'id_token': idToken,
          'access_token': accessToken,
        }),
      ).timeout(OcrConfig.timeoutDuration);

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? '구글 로그인에 실패했습니다.');
      }
    } catch (e) {
      rethrow;
    }
  }

  static Future<void> signOut() async {
    await _googleSignIn.signOut();
  }
}