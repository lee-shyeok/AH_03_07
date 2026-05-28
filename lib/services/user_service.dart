import 'dart:convert';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';
import 'auth_service.dart';

// ════════════════════════════════════════════════════════════
// 유저 상세 모델
// ════════════════════════════════════════════════════════════

class UserProfile {
  final String id;
  final String email;
  final String name;
  final String? phone;
  final String? birthDate;
  final double? height;
  final double? weight;
  final String userType;
  final List<String> chronicDiseases;
  final List<String> allergies;

  const UserProfile({
    required this.id,
    required this.email,
    required this.name,
    this.phone,
    this.birthDate,
    this.height,
    this.weight,
    required this.userType,
    required this.chronicDiseases,
    required this.allergies,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    List<String> parseStringOrList(dynamic value) {
      if (value == null) return [];
      if (value is List) return List<String>.from(value);
      if (value is String) {
        return value.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
      }
      return [];
    }

    return UserProfile(
      id: json['id']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      phone: json['phone_number']?.toString(),
      birthDate: json['birth_date']?.toString(),
      height: (json['height'] as num?)?.toDouble(),
      weight: (json['weight'] as num?)?.toDouble(),
      userType: json['user_type']?.toString() ?? 'general',
      chronicDiseases: parseStringOrList(json['chronic_diseases']),
      allergies: parseStringOrList(json['allergy_info']),
    );
  }
}

// ════════════════════════════════════════════════════════════
// 유저 서비스
// ════════════════════════════════════════════════════════════

class UserService {
  final TokenStorage _tokenStorage;
  final http.Client _client;
  bool _disposed = false;

  UserService({
    required TokenStorage tokenStorage,
    http.Client? client,
  })  : _tokenStorage = tokenStorage,
        _client = client ?? http.Client();

  void _assertNotDisposed() {
    if (_disposed) throw StateError('UserService가 이미 해제됐습니다.');
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
    if (statusCode == 401) throw AuthException(message);
    throw AuthException(message);
  }

  Future<Map<String, String>> _authHeaders() async {
    final token = await _tokenStorage.getAccessToken();
    if (token == null) throw const AuthException('로그인이 필요합니다.');
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, String>> _refreshAndGetHeaders() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null) {
      throw const AuthException('세션이 만료됐습니다. 다시 로그인해주세요.');
    }
    final response = await _client.post(
      Uri.parse('${OcrConfig.baseUrl}/v1/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 200) {
      final json = _parseBody(response.body);
      final newToken = json['access_token'] as String?;
      if (newToken == null) throw const AuthException('토큰 갱신에 실패했습니다.');
      await _tokenStorage.saveAccessToken(newToken);
      return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $newToken',
      };
    }
    throw const AuthException('세션이 만료됐습니다. 다시 로그인해주세요.');
  }

  /// GET /users/me
  Future<UserProfile> getMe() async {
    _assertNotDisposed();
    var headers = await _authHeaders();
    var response = await _client.get(
      Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
      headers: headers,
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
        headers: headers,
      ).timeout(OcrConfig.timeoutDuration);
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 200) return UserProfile.fromJson(json);
    _handleError(json, response.statusCode);
  }

  /// PATCH /users/me
  Future<void> patchMe(Map<String, dynamic> fields) async {
    _assertNotDisposed();
    final body = jsonEncode(fields);
    var headers = await _authHeaders();
    var response = await _client.patch(
      Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
      headers: headers,
      body: body,
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await _client.patch(
        Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
        headers: headers,
        body: body,
      ).timeout(OcrConfig.timeoutDuration);
    }
    if (response.statusCode == 200) return;
    final json = _parseBody(response.body);
    _handleError(json, response.statusCode);
  }

  /// DELETE /users/me
  Future<void> deleteMe(String password) async {
    _assertNotDisposed();
    final body = jsonEncode({'password': password});
    var headers = await _authHeaders();
    var response = await _client.delete(
      Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
      headers: headers,
      body: body,
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await _client.delete(
        Uri.parse('${OcrConfig.baseUrl}/v1/users/me'),
        headers: headers,
        body: body,
      ).timeout(OcrConfig.timeoutDuration);
    }
    if (response.statusCode == 200 || response.statusCode == 204) {
      await _tokenStorage.deleteAll();
      return;
    }
    final json = _parseBody(response.body);
    _handleError(json, response.statusCode);
  }

  void dispose() {
    if (_disposed) return;
    _client.close();
    _disposed = true;
  }
}