import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../services/notification_service.dart';
import '../services/ocr_service.dart';
import 'services/notification_service.dart';
import 'services/ocr_service.dart';

// ════════════════════════════════════════════════════════════
// REQ-NOTI-001: 복약 알림 설정
// ════════════════════════════════════════════════════════════

class NotificationSettingsPage extends StatefulWidget {
  final TokenStorage tokenStorage;
  final String medicationId;
  final String medicationName;
  final String? medicationType; // "자가면역" 등

  const NotificationSettingsPage({
    super.key,
    required this.tokenStorage,
    required this.medicationId,
    required this.medicationName,
    this.medicationType,
  });

  @override
  State<NotificationSettingsPage> createState() =>
      _NotificationSettingsPageState();
}

class _NotificationSettingsPageState extends State<NotificationSettingsPage> {
  late final NotificationService _service;

  // ── 상태 ──
  bool _loading = true;
  bool _saving = false;
  String? _error;

  // 알림 설정 값
  bool _isEnabled = true;
  TimeOfDay _alertTime = const TimeOfDay(hour: 9, minute: 0);
  DateTime _startDate = DateTime.now();
  DateTime _endDate = DateTime.now().add(const Duration(days: 90));
  final List<String> _weekdays = []; // 빈 배열 = 매일
  final Set<String> _channels = {'push'};
  bool _preAlertEnabled = false;
  bool _missedAlertEnabled = false;

  static const _weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];
  static const _weekdayCodes = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

  @override
  void initState() {
    super.initState();
    _service = NotificationService(tokenStorage: widget.tokenStorage);
    _loadSettings();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    try {
      final settings = await _service.getSettings();
      final existing = settings.where(
        (s) => s.medicationId == widget.medicationId,
      );
      if (existing.isNotEmpty) {
        final s = existing.first;
        final parts = s.alertTime.split(':');
        setState(() {
          _isEnabled = s.isEnabled;
          _alertTime = TimeOfDay(
            hour: int.tryParse(parts[0]) ?? 9,
            minute: int.tryParse(parts[1]) ?? 0,
          );
          if (s.startDate.isNotEmpty) {
            _startDate = DateTime.tryParse(s.startDate) ?? _startDate;
          }
          if (s.endDate.isNotEmpty) {
            _endDate = DateTime.tryParse(s.endDate) ?? _endDate;
          }
          _weekdays
            ..clear()
            ..addAll(s.weekdays);
          _channels
            ..clear()
            ..addAll(s.channels);
          _preAlertEnabled = s.preAlertEnabled;
          _missedAlertEnabled = s.missedAlertEnabled;
        });
      }
    } on AuthException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      // 설정 없으면 기본값 사용
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final setting = NotificationSetting(
        medicationId: widget.medicationId,
        medicationName: widget.medicationName,
        isEnabled: _isEnabled,
        alertTime:
            '${_alertTime.hour.toString().padLeft(2, '0')}:${_alertTime.minute.toString().padLeft(2, '0')}',
        startDate:
            '${_startDate.year}-${_startDate.month.toString().padLeft(2, '0')}-${_startDate.day.toString().padLeft(2, '0')}',
        endDate:
            '${_endDate.year}-${_endDate.month.toString().padLeft(2, '0')}-${_endDate.day.toString().padLeft(2, '0')}',
        weekdays: List.from(_weekdays),
        channels: _channels.toList(),
        preAlertEnabled: _preAlertEnabled,
        missedAlertEnabled: _missedAlertEnabled,
      );
      await _service.saveSettings(setting);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('알림 설정이 저장됐습니다.'),
            backgroundColor: Color(0xFF2ECC71),
          ),
        );
        Navigator.pop(context, true);
      }
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('저장 중 오류가 발생했습니다.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _alertTime,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: false),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _alertTime = picked);
  }

  Future<void> _pickDate({required bool isStart}) async {
    final initial = isStart ? _startDate : _endDate;
    final first = isStart ? DateTime(2020) : _startDate;
    final last = DateTime(2030);
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: first,
      lastDate: last,
      locale: const Locale('ko'),
    );
    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
          if (_endDate.isBefore(_startDate)) _endDate = _startDate;
        } else {
          _endDate = picked;
        }
      });
    }
  }

  String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';

  String _formatTime(TimeOfDay t) {
    final h = t.hour;
    final m = t.minute.toString().padLeft(2, '0');
    final period = h < 12 ? '오전' : '오후';
    final hour12 = h == 0 ? 12 : (h > 12 ? h - 12 : h);
    return '$period $hour12:$m';
  }

  String _weekdaySummary() {
    if (_weekdays.isEmpty) return '매일';
    final sorted = _weekdays
        .map((c) => _weekdayCodes.indexOf(c))
        .where((i) => i >= 0)
        .toList()
      ..sort();
    return sorted.map((i) => '${_weekdayLabels[i]}요일').join(', ');
  }

  // ── 색상 상수 ──
  static const _green = Color(0xFF2ECC71);
  static const _greenLight = Color(0xFFE8F8F0);
  static const _greenBorder = Color(0xFFB7EACF);
  static const _bg = Color(0xFFF8FAF8);
  static const _cardBg = Colors.white;
  static const _textPrimary = Color(0xFF1A1A1A);
  static const _textSecondary = Color(0xFF888888);
  static const _divider = Color(0xFFF0F0F0);

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
          '복약 알림 설정',
          style: TextStyle(
            color: _textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _green))
          : _error != null
              ? _buildError()
              : _buildBody(),
      bottomNavigationBar: _loading || _error != null
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                child: SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _saving ? null : _save,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _green,
                      disabledBackgroundColor: _green.withOpacity(0.5),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      elevation: 0,
                    ),
                    child: _saving
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 2.5,
                            ),
                          )
                        : const Text(
                            '저장하기',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(_error!, style: const TextStyle(color: _textSecondary)),
          const SizedBox(height: 16),
          TextButton(
            onPressed: () {
              setState(() {
                _error = null;
                _loading = true;
              });
              _loadSettings();
            },
            child: const Text('다시 시도', style: TextStyle(color: _green)),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 약품 헤더 카드 ──
          _buildMedCard(),
          const SizedBox(height: 24),

          // ── 알림 설정 ──
          _sectionLabel('알림 설정'),
          const SizedBox(height: 8),
          _buildSettingsCard([
            _buildToggleRow(
              label: '알림 받기',
              value: _isEnabled,
              onChanged: (v) => setState(() => _isEnabled = v),
            ),
            _buildDivider(),
            _buildTapRow(
              label: '알림 시간',
              trailing: Text(
                _formatTime(_alertTime),
                style: const TextStyle(
                  color: _green,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: _isEnabled ? _pickTime : null,
            ),
            _buildDivider(),
            _buildTapRow(
              label: '반복',
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _weekdaySummary(),
                    style: const TextStyle(
                      color: _green,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 4),
                  const Icon(Icons.keyboard_arrow_down,
                      color: _green, size: 18),
                ],
              ),
              onTap: _isEnabled ? _showWeekdayPicker : null,
            ),
          ]),
          const SizedBox(height: 20),

          // ── 기간 설정 ──
          _sectionLabel('복약 기간'),
          const SizedBox(height: 8),
          _buildSettingsCard([
            _buildTapRow(
              label: '시작일',
              trailing: Text(
                _formatDate(_startDate),
                style: const TextStyle(
                  color: _green,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: _isEnabled ? () => _pickDate(isStart: true) : null,
            ),
            _buildDivider(),
            _buildTapRow(
              label: '종료일',
              trailing: Text(
                _formatDate(_endDate),
                style: const TextStyle(
                  color: _green,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: _isEnabled ? () => _pickDate(isStart: false) : null,
            ),
          ]),
          const SizedBox(height: 20),

          // ── 알림 옵션 ──
          _sectionLabel('알림 옵션'),
          const SizedBox(height: 8),
          _buildSettingsCard([
            _buildToggleRowWithSub(
              label: '5분 전 미리 알림',
              sub: '복용 시간 5분 전 추가 알림',
              value: _preAlertEnabled,
              onChanged: _isEnabled
                  ? (v) => setState(() => _preAlertEnabled = v)
                  : null,
            ),
            _buildDivider(),
            _buildToggleRowWithSub(
              label: '미복용 시 재알림',
              sub: '30분 후 재알림',
              value: _missedAlertEnabled,
              onChanged: _isEnabled
                  ? (v) => setState(() => _missedAlertEnabled = v)
                  : null,
            ),
          ]),
          const SizedBox(height: 20),

          // ── 알림 채널 ──
          _sectionLabel('알림 채널'),
          const SizedBox(height: 8),
          _buildSettingsCard([
            _buildCheckRow(
              label: '앱 푸시',
              checked: _channels.contains('push'),
              onTap: _isEnabled
                  ? () => _toggleChannel('push')
                  : null,
            ),
            _buildDivider(),
            _buildCheckRow(
              label: '카카오톡',
              checked: _channels.contains('kakao'),
              onTap: _isEnabled
                  ? () => _toggleChannel('kakao')
                  : null,
            ),
            _buildDivider(),
            _buildCheckRow(
              label: '이메일',
              checked: _channels.contains('email'),
              onTap: _isEnabled
                  ? () => _toggleChannel('email')
                  : null,
            ),
          ]),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  void _toggleChannel(String channel) {
    setState(() {
      if (_channels.contains(channel)) {
        if (_channels.length > 1) _channels.remove(channel);
      } else {
        _channels.add(channel);
      }
    });
  }

  void _showWeekdayPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setInner) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '반복 요일',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                      color: _textPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '선택하지 않으면 매일 알림을 받습니다.',
                    style: TextStyle(fontSize: 13, color: _textSecondary),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: List.generate(7, (i) {
                      final code = _weekdayCodes[i];
                      final selected = _weekdays.contains(code);
                      return GestureDetector(
                        onTap: () {
                          setInner(() {
                            if (selected) {
                              _weekdays.remove(code);
                            } else {
                              _weekdays.add(code);
                            }
                          });
                          setState(() {});
                        },
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: selected ? _green : _bg,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: selected ? _green : const Color(0xFFDDDDDD),
                            ),
                          ),
                          child: Center(
                            child: Text(
                              _weekdayLabels[i],
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: selected ? Colors.white : _textPrimary,
                              ),
                            ),
                          ),
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(ctx),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _green,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: 0,
                      ),
                      child: const Text(
                        '확인',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  // ── 공통 위젯 ──

  Widget _buildMedCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: const Color(0xFFF0E8FF),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.medication_rounded,
                color: Color(0xFF7C5CCF), size: 26),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.medicationName,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: _textPrimary,
                  ),
                ),
                if (widget.medicationType != null) ...[
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF7C5CCF),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      widget.medicationType!,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 13,
        color: _textSecondary,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildSettingsCard(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: _cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Column(children: children),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 1, thickness: 1, color: _divider,
        indent: 16, endIndent: 16);
  }

  Widget _buildToggleRow({
    required String label,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Padding(
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
            onChanged: onChanged,
            activeColor: _green,
          ),
        ],
      ),
    );
  }

  Widget _buildToggleRowWithSub({
    required String label,
    required String sub,
    required bool value,
    ValueChanged<bool>? onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                        color: _textPrimary)),
                const SizedBox(height: 2),
                Text(sub,
                    style: const TextStyle(
                        fontSize: 12, color: _textSecondary)),
              ],
            ),
          ),
          CupertinoSwitch(
            value: value,
            onChanged: onChanged,
            activeColor: _green,
          ),
        ],
      ),
    );
  }

  Widget _buildTapRow({
    required String label,
    required Widget trailing,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    color: onTap != null ? _textPrimary : _textSecondary)),
            trailing,
          ],
        ),
      ),
    );
  }

  Widget _buildCheckRow({
    required String label,
    required bool checked,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                    color: onTap != null ? _textPrimary : _textSecondary)),
            Container(
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                color: checked ? _green : Colors.transparent,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(
                    color: checked ? _green : const Color(0xFFCCCCCC),
                    width: 1.5),
              ),
              child: checked
                  ? const Icon(Icons.check, color: Colors.white, size: 15)
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}