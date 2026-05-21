import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';

class NotificationSettingsPage extends StatefulWidget {
  const NotificationSettingsPage({super.key});

  @override
  State<NotificationSettingsPage> createState() =>
      _NotificationSettingsPageState();
}

class _NotificationSettingsPageState
    extends State<NotificationSettingsPage> {
  final _client = http.Client();

  bool _isLoading = true;
  bool _isSaving = false;

  List<Map<String, dynamic>> _reminders = [];
  bool _medicationEnabled = true;
  bool _guideEnabled = true;
  bool _appEnabled = true;
  bool _emailEnabled = false;

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

  void _handleUnauthorized() {
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => LoginPage(
          onLoginSuccess: () {
            Navigator.of(context).pushAndRemoveUntil(
              PageRouteBuilder(
                pageBuilder: (_, __, ___) => const MainPage(),
                transitionsBuilder: (_, anim, __, child) =>
                    FadeTransition(opacity: anim, child: child),
                transitionDuration: const Duration(milliseconds: 400),
              ),
              (route) => false,
            );
          },
        ),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
        transitionDuration: const Duration(milliseconds: 400),
      ),
      (route) => false,
    );
  }

  // 알림 설정 + 복약 알림 목록 동시 로드
  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

      // 알림 설정 조회
      final settingResponse = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/notification-settings'),
        headers: headers,
      ).timeout(OcrConfig.timeoutDuration);

      // 복약 알림 목록 조회
      final reminderResponse = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/reminders'),
        headers: headers,
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (settingResponse.statusCode == 401 ||
          reminderResponse.statusCode == 401) {
        _handleUnauthorized();
        return;
      }

      if (settingResponse.statusCode == 200) {
        final data = jsonDecode(settingResponse.body);
        setState(() {
          _medicationEnabled = data['medication_enabled'] ?? true;
          _guideEnabled = data['guide_enabled'] ?? true;
          _appEnabled = data['app_enabled'] ?? true;
          _emailEnabled = data['email_enabled'] ?? false;
        });
      }

      if (reminderResponse.statusCode == 200) {
        final data = jsonDecode(reminderResponse.body);
        setState(() {
          _reminders = List<Map<String, dynamic>>.from(
              data['items'] ?? []);
        });
      }

      setState(() => _isLoading = false);
    } catch (_) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      _showSnackBar('설정을 불러오지 못했습니다.');
    }
  }

  // 복약 알림 등록 (POST /v1/reminders)
  Future<void> _saveReminder(Map<String, dynamic> reminder) async {
    setState(() => _isSaving = true);

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final response = await _client.post(
        Uri.parse('${OcrConfig.baseUrl}/v1/reminders'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(reminder),
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 201) {
        _showSnackBar('복약 알림이 저장됐습니다.');
        _loadSettings();
      } else if (response.statusCode == 401) {
        _handleUnauthorized();
      } else {
        _showSnackBar('저장에 실패했습니다.');
      }
    } catch (_) {
      if (!mounted) return;
      _showSnackBar('네트워크 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  // 복약 알림 삭제 (DELETE /v1/reminders/{id})
  Future<void> _deleteReminder(int id) async {
    try {
      final token = await _getToken();
      if (token == null) return;

      final response = await _client.delete(
        Uri.parse('${OcrConfig.baseUrl}/v1/reminders/$id'),
        headers: {'Authorization': 'Bearer $token'},
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 204) {
        setState(() => _reminders.removeWhere((r) => r['id'] == id));
        _showSnackBar('알림이 삭제됐습니다.');
      } else {
        _showSnackBar('삭제에 실패했습니다.');
      }
    } catch (_) {
      if (!mounted) return;
      _showSnackBar('오류가 발생했습니다.');
    }
  }

  // 알림 설정 ON/OFF (PATCH /v1/notification-settings)
  Future<void> _updateSetting(String key, bool value) async {
    try {
      final token = await _getToken();
      if (token == null) return;

      final response = await _client.patch(
        Uri.parse('${OcrConfig.baseUrl}/v1/notification-settings'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({key: value}),
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 401) {
        _handleUnauthorized();
      } else if (response.statusCode != 200) {
        _showSnackBar('설정 변경에 실패했습니다.');
        // 실패 시 원래 값으로 되돌리기
        setState(() {
          if (key == 'medication_enabled') _medicationEnabled = !value;
          if (key == 'guide_enabled') _guideEnabled = !value;
          if (key == 'app_enabled') _appEnabled = !value;
          if (key == 'email_enabled') _emailEnabled = !value;
        });
      }
    } catch (_) {
      if (!mounted) return;
      _showSnackBar('오류가 발생했습니다.');
    }
  }

  void _showSnackBar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  void _showAddReminderDialog() {
    final drugNameController = TextEditingController();
    final timeController = TextEditingController(text: '08:00');
    List<String> selectedChannels = ['app'];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 24,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('복약 알림 추가',
                      style: TextStyle(
                          fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 약품명
              const Text('약품명',
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                controller: drugNameController,
                decoration: InputDecoration(
                  hintText: '약품명 입력',
                  hintStyle:
                      const TextStyle(color: Colors.grey, fontSize: 14),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: Colors.grey.shade300),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: Colors.grey.shade300),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide:
                        const BorderSide(color: Color(0xFFFF8C00)),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                ),
              ),
              const SizedBox(height: 16),

              // 알림 시각
              const Text('알림 시각',
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              GestureDetector(
                onTap: () async {
                  final picked = await showTimePicker(
                    context: context,
                    initialTime: TimeOfDay.now(),
                    builder: (ctx, child) => Theme(
                      data: Theme.of(ctx).copyWith(
                        colorScheme: const ColorScheme.light(
                          primary: Color(0xFFFF8C00),
                        ),
                      ),
                      child: child!,
                    ),
                  );
                  if (picked != null) {
                    setModalState(() {
                      timeController.text =
                          '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
                    });
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey.shade300),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.access_time,
                          color: Color(0xFFFF8C00), size: 20),
                      const SizedBox(width: 8),
                      Text(timeController.text,
                          style: const TextStyle(
                              fontSize: 16, color: Colors.black87)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 알림 채널
              const Text('알림 채널',
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildChannelChip(
                    label: '앱 알림',
                    value: 'app',
                    selected: selectedChannels.contains('app'),
                    onTap: () => setModalState(() {
                      selectedChannels.contains('app')
                          ? selectedChannels.remove('app')
                          : selectedChannels.add('app');
                    }),
                  ),
                  const SizedBox(width: 8),
                  _buildChannelChip(
                    label: '이메일',
                    value: 'email',
                    selected: selectedChannels.contains('email'),
                    onTap: () => setModalState(() {
                      selectedChannels.contains('email')
                          ? selectedChannels.remove('email')
                          : selectedChannels.add('email');
                    }),
                  ),
                  const SizedBox(width: 8),
                  _buildChannelChip(
                    label: 'SMS',
                    value: 'sms',
                    selected: selectedChannels.contains('sms'),
                    onTap: () => setModalState(() {
                      selectedChannels.contains('sms')
                          ? selectedChannels.remove('sms')
                          : selectedChannels.add('sms');
                    }),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // 저장 버튼
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (drugNameController.text.trim().isEmpty) {
                      _showSnackBar('약품명을 입력해주세요.');
                      return;
                    }
                    if (selectedChannels.isEmpty) {
                      _showSnackBar('알림 채널을 하나 이상 선택해주세요.');
                      return;
                    }
                    Navigator.pop(context);
                    _saveReminder({
                      'drug_name': drugNameController.text.trim(),
                      'remind_times': [timeController.text],
                      'start_date': DateTime.now()
                          .toIso8601String()
                          .split('T')[0],
                      'weekdays': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
                      'channels': List<String>.from(selectedChannels),
                    });
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFF8C00),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                    elevation: 0,
                  ),
                  child: const Text('저장',
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChannelChip({
    required String label,
    required String value,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected
              ? const Color(0xFFFF8C00).withOpacity(0.1)
              : Colors.grey.shade100,
          border: Border.all(
            color: selected
                ? const Color(0xFFFF8C00)
                : Colors.grey.shade300,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? const Color(0xFFFF8C00) : Colors.grey,
            fontSize: 13,
            fontWeight:
                selected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios,
              color: Colors.black87, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          '알림 설정',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        centerTitle: false,
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(
                  color: Color(0xFFFF8C00)))
          : RefreshIndicator(
              color: const Color(0xFFFF8C00),
              onRefresh: _loadSettings,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // 복약 알림 섹션
                  _buildSectionHeader(
                    title: '복약 알림',
                    icon: Icons.medication_outlined,
                    trailing: _isSaving
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              color: Color(0xFFFF8C00),
                              strokeWidth: 2,
                            ),
                          )
                        : IconButton(
                            icon: const Icon(
                                Icons.add_circle_outline,
                                color: Color(0xFFFF8C00)),
                            onPressed: _showAddReminderDialog,
                          ),
                  ),
                  const SizedBox(height: 8),
                  _reminders.isEmpty
                      ? _buildEmptyReminder()
                      : Column(
                          children: _reminders
                              .map((r) => _buildReminderCard(r))
                              .toList(),
                        ),

                  const SizedBox(height: 20),

                  // 알림 채널 설정
                  _buildSectionHeader(
                    title: '알림 채널 설정',
                    icon: Icons.notifications_outlined,
                  ),
                  const SizedBox(height: 8),
                  _buildToggleCard(
                    title: '앱 알림',
                    subtitle: '앱 내 푸시 알림',
                    value: _appEnabled,
                    onChanged: (v) {
                      setState(() => _appEnabled = v);
                      _updateSetting('app_enabled', v);
                    },
                  ),
                  const SizedBox(height: 8),
                  _buildToggleCard(
                    title: '가이드 알림',
                    subtitle: '새 건강 가이드 업데이트 시 알림',
                    value: _guideEnabled,
                    onChanged: (v) {
                      setState(() => _guideEnabled = v);
                      _updateSetting('guide_enabled', v);
                    },
                  ),
                  const SizedBox(height: 8),
                  _buildToggleCard(
                    title: '복약 알림',
                    subtitle: '복약 시간 알림 활성화',
                    value: _medicationEnabled,
                    onChanged: (v) {
                      setState(() => _medicationEnabled = v);
                      _updateSetting('medication_enabled', v);
                    },
                  ),
                  const SizedBox(height: 8),
                  _buildToggleCard(
                    title: '이메일 알림',
                    subtitle: '이메일로 알림 받기',
                    value: _emailEnabled,
                    onChanged: (v) {
                      setState(() => _emailEnabled = v);
                      _updateSetting('email_enabled', v);
                    },
                  ),

                  const SizedBox(height: 24),

                  // 안내 문구
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color:
                          const Color(0xFFFF8C00).withOpacity(0.05),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: const Color(0xFFFF8C00).withOpacity(0.2),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.info_outline,
                            color: Color(0xFFFF8C00), size: 18),
                        const SizedBox(width: 8),
                        const Expanded(
                          child: Text(
                            '모든 알림은 사용자 동의 기반으로 활성화·해제됩니다.',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey,
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
    );
  }

  Widget _buildSectionHeader({
    required String title,
    required IconData icon,
    Widget? trailing,
  }) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFFFF8C00), size: 20),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
        const Spacer(),
        if (trailing != null) trailing,
      ],
    );
  }

  Widget _buildEmptyReminder() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(Icons.notifications_off_outlined,
              size: 40, color: Colors.grey.shade300),
          const SizedBox(height: 12),
          const Text('등록된 복약 알림이 없습니다.',
              style: TextStyle(color: Colors.grey, fontSize: 14)),
          const SizedBox(height: 4),
          const Text('+ 버튼을 눌러 알림을 추가해보세요.',
              style: TextStyle(color: Colors.grey, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildReminderCard(Map<String, dynamic> reminder) {
    final id = reminder['id'] as int? ?? 0;
    final drugName = reminder['drug_name'] as String? ?? '약품명 없음';
    final remindTimes = (reminder['remind_times'] as List?)
            ?.cast<String>() ??
        [];
    final channels =
        (reminder['channels'] as List?)?.cast<String>() ?? [];
    final isActive = reminder['is_active'] as bool? ?? true;

    const channelLabels = {
      'app': '앱',
      'email': '이메일',
      'sms': 'SMS',
      'kakao': '카카오',
    };

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: isActive
                  ? const Color(0xFFFF8C00).withOpacity(0.1)
                  : Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.access_alarm,
                color: isActive
                    ? const Color(0xFFFF8C00)
                    : Colors.grey,
                size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(drugName,
                    style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87)),
                const SizedBox(height: 4),
                Text(
                  remindTimes.join(', '),
                  style: const TextStyle(
                      fontSize: 13, color: Colors.grey),
                ),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 4,
                  children: channels
                      .map((c) => Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFF8C00)
                                  .withOpacity(0.1),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              channelLabels[c] ?? c,
                              style: const TextStyle(
                                  fontSize: 11,
                                  color: Color(0xFFFF8C00)),
                            ),
                          ))
                      .toList(),
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.delete_outline,
                color: Colors.grey.shade400),
            onPressed: () => _showDeleteConfirm(id, drugName),
          ),
        ],
      ),
    );
  }

  Widget _buildToggleCard({
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: Colors.black87)),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: TextStyle(
                        fontSize: 12, color: Colors.grey.shade500)),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: const Color(0xFFFF8C00),
          ),
        ],
      ),
    );
  }

  void _showDeleteConfirm(int id, String drugName) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16)),
        title: const Text('알림 삭제',
            style: TextStyle(fontWeight: FontWeight.bold)),
        content: Text('$drugName 알림을 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소',
                style: TextStyle(color: Colors.grey)),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteReminder(id);
            },
            child: const Text('삭제',
                style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}