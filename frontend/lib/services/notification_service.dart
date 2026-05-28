import 'dart:convert';
import 'package:http/http.dart' as http;
import 'ocr_service.dart';

// ════════════════════════════════════════════════════════════
// 알림 설정 모델
// ════════════════════════════════════════════════════════════

class NotificationSetting {
  final String medicationId;
  final String medicationName;
  final bool isEnabled;
  final String alertTime;       // "HH:mm" 형식
  final String startDate;       // "yyyy-MM-dd"
  final String endDate;         // "yyyy-MM-dd"
  final List<String> weekdays;  // ["MON","TUE",...] 비어있으면 매일
  final List<String> channels;  // ["push","kakao","email"]
  final bool preAlertEnabled;   // 5분 전 알림
  final bool missedAlertEnabled; // 미복용 재알림

  const NotificationSetting({
    required this.medicationId,
    required this.medicationName,
    required this.isEnabled,
    required this.alertTime,
    required this.startDate,
    required this.endDate,
    required this.weekdays,
    required this.channels,
    required this.preAlertEnabled,
    required this.missedAlertEnabled,
  });

  factory NotificationSetting.fromJson(Map<String, dynamic> json) {
    return NotificationSetting(
      medicationId: json['medication_id']?.toString() ?? '',
      medicationName: json['medication_name']?.toString() ?? '',
      isEnabled: json['is_enabled'] as bool? ?? false,
      alertTime: json['alert_time']?.toString() ?? '09:00',
      startDate: json['start_date']?.toString() ?? '',
      endDate: json['end_date']?.toString() ?? '',
      weekdays: List<String>.from(json['weekdays'] as List? ?? []),
      channels: List<String>.from(json['channels'] as List? ?? ['push']),
      preAlertEnabled: json['pre_alert_enabled'] as bool? ?? false,
      missedAlertEnabled: json['missed_alert_enabled'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'medication_id': medicationId,
        'is_enabled': isEnabled,
        'alert_time': alertTime,
        'start_date': startDate,
        'end_date': endDate,
        'weekdays': weekdays,
        'channels': channels,
        'pre_alert_enabled': preAlertEnabled,
        'missed_alert_enabled': missedAlertEnabled,
      };

  NotificationSetting copyWith({
    bool? isEnabled,
    String? alertTime,
    String? startDate,
    String? endDate,
    List<String>? weekdays,
    List<String>? channels,
    bool? preAlertEnabled,
    bool? missedAlertEnabled,
  }) {
    return NotificationSetting(
      medicationId: medicationId,
      medicationName: medicationName,
      isEnabled: isEnabled ?? this.isEnabled,
      alertTime: alertTime ?? this.alertTime,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      weekdays: weekdays ?? this.weekdays,
      channels: channels ?? this.channels,
      preAlertEnabled: preAlertEnabled ?? this.preAlertEnabled,
      missedAlertEnabled: missedAlertEnabled ?? this.missedAlertEnabled,
    );
  }
}

// ════════════════════════════════════════════════════════════
// 알림 서비스
// ════════════════════════════════════════════════════════════

class NotificationService {
  final TokenStorage _tokenStorage;
  final http.Client _client;
  bool _disposed = false;

  NotificationService({
    required TokenStorage tokenStorage,
    http.Client? client,
  })  : _tokenStorage = tokenStorage,
        _client = client ?? http.Client();

  void _assertNotDisposed() {
    if (_disposed) throw StateError('NotificationService가 이미 해제됐습니다.');
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

  /// GET /notifications/settings - 알림 설정 목록 조회
  Future<List<NotificationSetting>> getSettings() async {
    _assertNotDisposed();
    var headers = await _authHeaders();
    var response = await _client.get(
      Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
      headers: headers,
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
        headers: headers,
      ).timeout(OcrConfig.timeoutDuration);
    }
    final json = _parseBody(response.body);
    if (response.statusCode == 200) {
      final list = json['settings'] as List? ?? [];
      return list
          .map((e) => NotificationSetting.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    _handleError(json, response.statusCode);
  }

  /// POST /notifications/settings - 알림 설정 저장
  Future<void> saveSettings(NotificationSetting setting) async {
    _assertNotDisposed();
    final body = jsonEncode(setting.toJson());
    var headers = await _authHeaders();
    var response = await _client.post(
      Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
      headers: headers,
      body: body,
    ).timeout(OcrConfig.timeoutDuration);
    if (response.statusCode == 401) {
      headers = await _refreshAndGetHeaders();
      response = await _client.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
        headers: headers,
        body: body,
      ).timeout(OcrConfig.timeoutDuration);
    }
    if (response.statusCode == 200 || response.statusCode == 201) return;
    final json = _parseBody(response.body);
    _handleError(json, response.statusCode);
  }

  void dispose() {
    if (!_disposed) {
      _client.close();
      _disposed = true;
    }
  }
}