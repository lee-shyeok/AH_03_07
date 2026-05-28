import 'dart:convert';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';

// ════════════════════════════════════════════════════════════
// 유저 모델
// ════════════════════════════════════════════════════════════

class UserModel {
  final String id;
  final String email;
  final String name;

  const UserModel({required this.id, required this.email, required this.name});

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
    );
  }
}

// ════════════════════════════════════════════════════════════
// Auth 서비스
// ════════════════════════════════════════════════════════════

class AuthService {
  final http.Client _client;
  final TokenStorage _tokenStorage;
  bool _disposed = false;

  AuthService({
    required TokenStorage tokenStorage,
    http.Client? client,
  })  : _tokenStorage = tokenStorage,
        _client = client ?? http.Client();

  void _assertNotDisposed() {
    if (_disposed) throw StateError('AuthService가 이미 해제됐습니다.');
  }

  Map<String, dynamic> _parseBody(String body) {
    try {
      return jsonDecode(body) as Map<String, dynamic>;
    } catch (_) {
      throw const AuthException('서버 응답을 처리할 수 없습니다.');
    }
  }

  Never _handleError(Map<String, dynamic> json, int statusCode) {
    final detail = json['detail'];
    String message = '오류가 발생했습니다.';
    if (detail is String) message = detail;
    if (detail is Map) message = (detail['message'] as String?) ?? message;
    throw AuthException(message);
  }

  bool _isTokenExpired(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return true;
      final payload = utf8.decode(
        base64Url.decode(base64Url.normalize(parts[1])),
      );
      final json = jsonDecode(payload) as Map<String, dynamic>;
      final exp = json['exp'] as int?;
      if (exp == null) return true;
      return DateTime.now().millisecondsSinceEpoch ~/ 1000 >= exp;
    } catch (_) {
      return true;
    }
  }

  Future<void> signup({
    required String email,
    required String password,
    required String name,
    required String birthDate,
  }) async {
    _assertNotDisposed();
    late http.Response response;
    try {
      response = await _client.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email.trim(),
          'password': password,
          'name': name.trim(),
          'birth_date': birthDate,
        }),
      ).timeout(OcrConfig.timeoutDuration);
    } catch (_) {
      throw const AuthException('네트워크 오류가 발생했습니다.');
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 201) {
      await _saveTokens(json);
    } else {
      _handleError(json, response.statusCode);
    }
  }

  Future<void> login(String email, String password) async {
    _assertNotDisposed();
    late http.Response response;
    try {
      response = await _client.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email.trim(),
          'password': password,
        }),
      ).timeout(OcrConfig.timeoutDuration);
    } catch (_) {
      throw const AuthException('네트워크 오류가 발생했습니다.');
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 200) {
      await _saveTokens(json);
    } else {
      _handleError(json, response.statusCode);
    }
  }

  Future<void> _saveTokens(Map<String, dynamic> json) async {
    final accessToken = json['access_token'] as String?;
    final refreshToken = json['refresh_token'] as String?;
    if (accessToken == null || refreshToken == null) {
      throw const AuthException('서버 응답에 토큰이 없습니다.');
    }
    try {
      await _tokenStorage.saveAccessToken(accessToken);
      await _tokenStorage.saveRefreshToken(refreshToken);
      final user = json['user'] as Map<String, dynamic>?;
      if (user != null) {
        final userModel = UserModel.fromJson(user);
        await _tokenStorage.saveUserId(userModel.id);
        await _tokenStorage.saveUserEmail(userModel.email);
      }
    } catch (_) {
      await _tokenStorage.deleteAll();
      throw const AuthException('로그인 정보 저장에 실패했습니다.');
    }
  }

  Future<void> logout() async {
    _assertNotDisposed();
    try {
      final token = await _tokenStorage.getAccessToken();
      if (token != null) {
        await _client.post(
          Uri.parse('${OcrConfig.baseUrl}/v1/auth/logout'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
        ).timeout(OcrConfig.timeoutDuration);
      }
    } catch (_) {}
    await _tokenStorage.deleteAll();
  }

  Future<bool> isLoggedIn() async {
    final token = await _tokenStorage.getAccessToken();
    if (token == null || token.isEmpty) return false;
    if (_isTokenExpired(token)) {
      try {
        await _tryRefreshToken();
        return true;
      } catch (_) {
        await _tokenStorage.deleteAll();
        return false;
      }
    }
    return true;
  }

  Future<void> _tryRefreshToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) throw const AuthException('리프레시 토큰 없음');
    final response = await _client.post(
      Uri.parse('${OcrConfig.baseUrl}/v1/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 200) {
      final json = _parseBody(response.body);
      final newToken = json['access_token'] as String?;
      if (newToken == null) throw const AuthException('토큰 갱신 실패');
      await _tokenStorage.saveAccessToken(newToken);
    } else {
      throw const AuthException('토큰 갱신 실패');
    }
  }

  void dispose() {
    if (!_disposed) {
      _client.close();
      _disposed = true;
    }
  }
}