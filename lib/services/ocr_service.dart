import 'dart:async';
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

// ════════════════════════════════════════════════════════════
// 예외 클래스
// ════════════════════════════════════════════════════════════

class OcrException implements Exception {
  final String code;
  final String message;
  const OcrException({required this.code, required this.message});
  @override
  String toString() => '[$code] $message';
}

class NetworkException implements Exception {
  final String message;
  const NetworkException(this.message);
  @override
  String toString() => '[NETWORK_ERROR] $message';
}

class AuthException implements Exception {
  final String message;
  const AuthException(this.message);
  @override
  String toString() => '[AUTH_ERROR] $message';
}

// ════════════════════════════════════════════════════════════
// 설정
// ════════════════════════════════════════════════════════════

class OcrConfig {
  static const baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'http://localhost/api',
  );
  static const allowedExtensions = ['jpg', 'jpeg', 'png'];
  static const maxFileSizeBytes = 5 * 1024 * 1024;
  static const timeoutDuration = Duration(seconds: 30);
  static const maxRetries = 3;
}

// ════════════════════════════════════════════════════════════
// 토큰 저장소 인터페이스
// ════════════════════════════════════════════════════════════

abstract class TokenStorage {
  Future<String?> getAccessToken();
  Future<String?> getRefreshToken();
  Future<void> saveAccessToken(String token);
  Future<void> saveRefreshToken(String token);
  Future<void> saveUserId(String id);
  Future<void> saveUserEmail(String email);
  Future<void> deleteAll();
}

// ════════════════════════════════════════════════════════════
// OCR 서비스
// ════════════════════════════════════════════════════════════

class OcrService {
  final TokenStorage _tokenStorage;
  final http.Client _client;
  bool _disposed = false;

  OcrService({required TokenStorage tokenStorage, http.Client? client})
      : _tokenStorage = tokenStorage,
        _client = client ?? http.Client();

  void _assertNotDisposed() {
    if (_disposed) throw StateError('OcrService가 이미 해제됐습니다.');
  }

  Future<void> _validateFile(File file) async {
    final ext = file.path.split('.').last.toLowerCase();
    if (!OcrConfig.allowedExtensions.contains(ext)) {
      throw OcrException(
        code: 'INVALID_FILE_TYPE',
        message: '${OcrConfig.allowedExtensions.join(', ')} 형식만 지원합니다.',
      );
    }
    final fileSize = await file.length();
    if (fileSize > OcrConfig.maxFileSizeBytes) {
      throw const OcrException(
        code: 'FILE_TOO_LARGE',
        message: '파일 크기는 5MB 이하여야 합니다.',
      );
    }
  }

  static final _uuidRegex = RegExp(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    caseSensitive: false,
  );

  void _validateUuid(String value, String fieldName) {
    if (!_uuidRegex.hasMatch(value)) {
      throw OcrException(code: 'INVALID_ID', message: '잘못된 $fieldName 형식입니다.');
    }
  }

  Map<String, dynamic> _parseBody(String body) {
    try {
      return jsonDecode(body) as Map<String, dynamic>;
    } catch (_) {
      throw const NetworkException('서버 응답을 처리할 수 없습니다.');
    }
  }

  Never _handleError(Map<String, dynamic> json, int statusCode) {
    final detail = json['detail'];
    String code = 'UNKNOWN_ERROR';
    String message = '알 수 없는 오류가 발생했습니다.';
    if (detail is Map) {
      code = (detail['code'] as String?) ?? code;
      message = (detail['message'] as String?) ?? message;
    } else if (detail is String) {
      message = detail;
    }
    if (statusCode == 401) throw AuthException(message);
    throw OcrException(code: code, message: message);
  }

  Future<Map<String, String>> _authHeaders({bool isMultipart = false}) async {
    final token = await _tokenStorage.getAccessToken();
    if (token == null) throw const AuthException('로그인이 필요합니다.');
    return {
      if (!isMultipart) 'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, String>> _refreshAndGetHeaders({bool isMultipart = false}) async {
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
        if (!isMultipart) 'Content-Type': 'application/json',
        'Authorization': 'Bearer $newToken',
      };
    }
    throw const AuthException('세션이 만료됐습니다. 다시 로그인해주세요.');
  }

  Future<T> _withRetry<T>(Future<T> Function() fn) async {
    int attempt = 0;
    while (true) {
      try {
        return await fn().timeout(
          OcrConfig.timeoutDuration,
          onTimeout: () => throw const NetworkException('요청 시간이 초과됐습니다.'),
        );
      } on AuthException { rethrow; }
      on OcrException { rethrow; }
      on NetworkException { rethrow; }
      catch (e) {
        attempt++;
        if (attempt >= OcrConfig.maxRetries) {
          throw NetworkException('네트워크 오류가 반복됩니다: $e');
        }
        await Future.delayed(Duration(seconds: attempt * 2));
      }
    }
  }

  Future<String> uploadDocument(File imageFile, String documentType) async {
    _assertNotDisposed();
    await _validateFile(imageFile);

    Future<http.Response> doRequest(Map<String, String> hdrs) async {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents'),
      )
        ..headers.addAll(hdrs)
        ..fields['document_type'] = documentType
        ..files.add(await http.MultipartFile.fromPath('file', imageFile.path));
      final streamed = await _client.send(request).timeout(
            OcrConfig.timeoutDuration,
            onTimeout: () => throw const NetworkException('업로드 시간이 초과됐습니다.'),
          );
      return http.Response.fromStream(streamed);
    }

    var headers = await _authHeaders(isMultipart: true);
    var response = await doRequest(headers);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders(isMultipart: true);
      response = await doRequest(headers);
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 201) return json['document_id'] as String;
    _handleError(json, response.statusCode);
  }

  Future<String> startOcrJob(String documentId) async {
    _assertNotDisposed();
    _validateUuid(documentId, 'documentId');

    Future<http.Response> doRequest(Map<String, String> hdrs) => _client
        .post(
          Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents/$documentId/ocr-jobs'),
          headers: hdrs,
        )
        .timeout(OcrConfig.timeoutDuration,
            onTimeout: () => throw const NetworkException('요청 시간이 초과됐습니다.'));

    var headers = await _authHeaders();
    var response = await doRequest(headers);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await doRequest(headers);
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 202) return json['job_id'] as String;
    _handleError(json, response.statusCode);
  }

  Future<Map<String, dynamic>> getOcrResult(String jobId) async {
    _assertNotDisposed();
    _validateUuid(jobId, 'jobId');

    return _withRetry(() async {
      var headers = await _authHeaders();
      var response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/ocr-jobs/$jobId'),
        headers: headers,
      );
      if (response.statusCode == 401) {
        headers = await _refreshAndGetHeaders();
        response = await _client.get(
          Uri.parse('${OcrConfig.baseUrl}/v1/ocr-jobs/$jobId'),
          headers: headers,
        );
      }
      final json = _parseBody(response.body);
      if (response.statusCode == 200) return json;
      _handleError(json, response.statusCode);
    });
  }

  Future<void> confirmOcrResult(String documentId, Map<String, dynamic> structuredData) async {
    _assertNotDisposed();
    _validateUuid(documentId, 'documentId');

    final body = jsonEncode({'structured_data': structuredData, 'user_confirmed': true});

    return _withRetry(() async {
      var headers = await _authHeaders();
      var response = await _client.put(
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents/$documentId/confirm'),
        headers: headers,
        body: body,
      );
      if (response.statusCode == 401) {
        headers = await _refreshAndGetHeaders();
        response = await _client.put(
          Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents/$documentId/confirm'),
          headers: headers,
          body: body,
        );
      }
      if (response.statusCode == 200) return;
      final json = _parseBody(response.body);
      _handleError(json, response.statusCode);
    });
  }

  void dispose() {
    if (!_disposed) {
      _client.close();
      _disposed = true;
    }
  }
}