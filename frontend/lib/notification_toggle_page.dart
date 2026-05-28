import 'dart:convert';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'services/ocr_service.dart';
import 'main.dart';

// ════════════════════════════════════════════════════════════
// REQ-NOTI-006: 알림 ON/OFF 설정 (유형별/채널별)
// ════════════════════════════════════════════════════════════

class NotificationTogglePage extends StatefulWidget {
  const NotificationTogglePage({super.key});

  @override
  State<NotificationTogglePage> createState() =>
      _NotificationTogglePageState();
}

class _NotificationTogglePageState extends State<NotificationTogglePage> {
  final _client = http.Client();
  bool _loading = true;
  bool _saving = false;

  // ── 알림 설정 ──
  bool _medicationAlert = true;
  bool _guideAlert = true;
  bool _marketingAlert = false;

  // ── 알림 채널 ──
  bool _pushChannel = true;
  bool _emailChannel = false;
  bool _kakaoChannel = true;

  static const _orange = Color(0xFFFF8C00);
  static const _bg = Color(0xFFF8F8F8);
  static const _cardBg = Colors.white;
  static const _textPrimary = Color(0xFF1A1A1A);
  static const _textSecondary = Color(0xFF888888);
  static const _divider = Color(0xFFF0F0F0);

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<String?> _getToken() async {
    return SecureTokenStorage().getAccessToken();
  }

  Future<void> _loadSettings() async {
    try {
      final token = await _getToken();
      if (token == null) return;

      final response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() {
          _medicationAlert = data['medication_alert'] as bool? ?? true;
          _guideAlert = data['guide_alert'] as bool? ?? true;
          _marketingAlert = data['marketing_alert'] as bool? ?? false;
          _pushChannel = data['push_channel'] as bool? ?? true;
          _emailChannel = data['email_channel'] as bool? ?? false;
          _kakaoChannel = data['kakao_channel'] as bool? ?? true;
        });
      }
      // 404나 다른 에러면 기본값 유지
    } catch (_) {
      // 기본값 유지
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _saveSettings() async {
    setState(() => _saving = true);
    try {
      final token = await _getToken();
      if (token == null) return;

      final response = await _client.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/notifications/settings'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'medication_alert': _medicationAlert,
          'guide_alert': _guideAlert,
          'marketing_alert': _marketingAlert,
          'push_channel': _pushChannel,
          'email_channel': _emailChannel,
          'kakao_channel': _kakaoChannel,
        }),
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('알림 설정이 저장됐습니다.'),
            backgroundColor: Color(0xFF2ECC71),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('저장에 실패했습니다.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('오류가 발생했습니다.'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
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
          icon: const Icon(Icons.chevron_left, color: _textPrimary, size: 28),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          '알림 설정',
          style: TextStyle(
              color: _textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.w600),
        ),
        centerTitle: false,
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: _orange))
          : SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── 알림 설정 ──
                  _sectionLabel('알림 설정'),
                  const SizedBox(height: 8),
                  _buildCard([
                    _buildToggleRow(
                      label: '복약 알림',
                      value: _medicationAlert,
                      onChanged: (v) =>
                          setState(() => _medicationAlert = v),
                    ),
                    _buildDivider(),
                    _buildToggleRow(
                      label: '가이드 확인 알림',
                      value: _guideAlert,
                      onChanged: (v) =>
                          setState(() => _guideAlert = v),
                    ),
                    _buildDivider(),
                    _buildToggleRow(
                      label: '마케팅 알림',
                      value: _marketingAlert,
                      onChanged: (v) =>
                          setState(() => _marketingAlert = v),
                    ),
                  ]),
                  const SizedBox(height: 20),

                  // ── 알림 채널 ──
                  _sectionLabel('알림 채널'),
                  const SizedBox(height: 8),
                  _buildCard([
                    _buildToggleRow(
                      label: '앱 알림',
                      value: _pushChannel,
                      onChanged: (v) =>
                          setState(() => _pushChannel = v),
                    ),
                    _buildDivider(),
                    _buildToggleRow(
                      label: '이메일',
                      value: _emailChannel,
                      onChanged: (v) =>
                          setState(() => _emailChannel = v),
                    ),
                    _buildDivider(),
                    _buildToggleRow(
                      label: '카카오톡',
                      value: _kakaoChannel,
                      onChanged: (v) =>
                          setState(() => _kakaoChannel = v),
                    ),
                  ]),
                  const SizedBox(height: 32),

                  // ── 저장 버튼 ──
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton(
                      onPressed: _saving ? null : _saveSettings,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _orange,
                        disabledBackgroundColor:
                            _orange.withOpacity(0.5),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14)),
                        elevation: 0,
                      ),
                      child: _saving
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(
                                  color: Colors.white, strokeWidth: 2.5),
                            )
                          : const Text(
                              '저장하기',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700),
                            ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _sectionLabel(String text) => Text(
        text,
        style: const TextStyle(
            fontSize: 13,
            color: _textSecondary,
            fontWeight: FontWeight.w500),
      );

  Widget _buildCard(List<Widget> children) => Container(
        decoration: BoxDecoration(
          color: _cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFE8E8E8)),
        ),
        child: Column(children: children),
      );

  Widget _buildDivider() => const Divider(
      height: 1, thickness: 1, color: _divider, indent: 16, endIndent: 16);

  Widget _buildToggleRow({
    required String label,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) =>
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    color: _textPrimary)),
            CupertinoSwitch(
              value: value,
              onChanged: _saving ? null : onChanged,
              activeColor: _orange,
            ),
          ],
        ),
      );
}