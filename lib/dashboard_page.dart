import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';
import 'chat_page.dart';
import 'ocr_history_page.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool _isLoading = true;
  bool _hasError = false;
  Map<String, dynamic>? _data;
  final _client = http.Client();

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<String?> _getToken() async {
    return SecureTokenStorage().getAccessToken();
  }

  Future<void> _loadDashboard() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/dashboard'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200) {
        setState(() {
          _data = jsonDecode(response.body) as Map<String, dynamic>;
          _isLoading = false;
        });
      } else if (response.statusCode == 401) {
        _handleUnauthorized();
      } else {
        setState(() {
          _hasError = true;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _hasError = true;
        _isLoading = false;
      });
    }
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

  void _openChat() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const ChatPage()),
    );
  }

  void _openOcrHistory() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const OcrHistoryPage()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          '홈',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.document_scanner_outlined,
                color: Color(0xFFFF8C00)),
            tooltip: 'OCR 내역',
            onPressed: _openOcrHistory,
          ),
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline,
                color: Color(0xFFFF8C00)),
            tooltip: '챗봇',
            onPressed: _openChat,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFFFF8C00)))
          : _hasError
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadDashboard,
                  color: const Color(0xFFFF8C00),
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildChatBanner(),
                        const SizedBox(height: 16),
                        _buildMedicationCard(),
                        const SizedBox(height: 16),
                        _buildRecentRecordsCard(),
                        const SizedBox(height: 16),
                        _buildRecentGuidesCard(),
                        const SizedBox(height: 16),
                        _buildPendingOcrCard(),
                        const SizedBox(height: 32),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildChatBanner() {
    return GestureDetector(
      onTap: _openChat,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFFF8C00), Color(0xFFFFAD00)],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFFF8C00).withOpacity(0.3),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: const Row(
          children: [
            Icon(Icons.smart_toy_outlined, color: Colors.white, size: 32),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'AI 건강 챗봇',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '복약, 생활습관 등 건강 관련 질문을 해보세요!',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('데이터를 불러오지 못했습니다.',
              style: TextStyle(color: Colors.grey, fontSize: 16)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadDashboard,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF8C00),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('다시 시도',
                style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title, IconData icon,
      {VoidCallback? onMore}) {
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
        if (onMore != null)
          GestureDetector(
            onTap: onMore,
            child: const Text(
              '전체보기',
              style: TextStyle(
                  fontSize: 12,
                  color: Color(0xFFFF8C00),
                  fontWeight: FontWeight.w600),
            ),
          ),
      ],
    );
  }

  Widget _buildCard({required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: child,
    );
  }

  Widget _buildMedicationCard() {
    final total = _data?['today_medication_reminders_total'] ?? 0;
    final remaining = _data?['today_medication_reminders_remaining'] ?? 0;

    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('오늘의 복약', Icons.medication_outlined),
          const SizedBox(height: 16),
          if (total == 0)
            const Text('오늘 복약 알림이 없습니다.',
                style: TextStyle(color: Colors.grey, fontSize: 14))
          else
            Row(
              children: [
                Expanded(
                  child: _buildMedicationStat(
                      '전체', total.toString(), const Color(0xFFFF8C00)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMedicationStat(
                    '남은 복약',
                    remaining.toString(),
                    remaining > 0 ? Colors.red : Colors.green,
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildMedicationStat(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.bold, color: color),
          ),
          const SizedBox(height: 4),
          Text(label,
              style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildRecentRecordsCard() {
    final records =
        (_data?['recent_records'] as List?)?.cast<Map<String, dynamic>>() ??
            [];

    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('최근 진료기록', Icons.medical_services_outlined),
          const SizedBox(height: 12),
          if (records.isEmpty)
            const Text('최근 진료기록이 없습니다.',
                style: TextStyle(color: Colors.grey, fontSize: 14))
          else
            ...records.map((r) => _buildRecordItem(r)),
        ],
      ),
    );
  }

  Widget _buildRecordItem(Map<String, dynamic> record) {
    final visitDate = record['visit_date'] as String? ?? '';
    final hospitalName = record['hospital_name'] as String? ?? '병원명 없음';
    final diagnosis = record['diagnosis'] as String? ?? '';
    final medCount = record['medication_count'] as int? ?? 0;

    String formattedDate = visitDate;
    try {
      final date = DateTime.parse(visitDate);
      formattedDate = DateFormat('yyyy.MM.dd').format(date);
    } catch (_) {}

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFFFF8C00).withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.local_hospital_outlined,
                color: Color(0xFFFF8C00), size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(hospitalName,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 14)),
                Text('$formattedDate · $diagnosis',
                    style:
                        const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
          Text('약 $medCount종',
              style: const TextStyle(
                  color: Color(0xFFFF8C00),
                  fontSize: 12,
                  fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildRecentGuidesCard() {
    final guides =
        (_data?['recent_guides'] as List?)?.cast<Map<String, dynamic>>() ??
            [];

    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('최근 안내문', Icons.article_outlined),
          const SizedBox(height: 12),
          if (guides.isEmpty)
            const Text('최근 안내문이 없습니다.',
                style: TextStyle(color: Colors.grey, fontSize: 14))
          else
            ...guides.map((g) => _buildGuideItem(g)),
        ],
      ),
    );
  }

  Widget _buildGuideItem(Map<String, dynamic> guide) {
    final diagnosis = guide['diagnosis'] as String? ?? '';
    final status = guide['status'] as String? ?? '';
    final createdAt = guide['created_at'] as String? ?? '';

    String formattedDate = createdAt;
    try {
      final date = DateTime.parse(createdAt);
      formattedDate = DateFormat('yyyy.MM.dd').format(date);
    } catch (_) {}

    Color statusColor = const Color(0xFFFF8C00);
    String statusText = '활성';
    if (status == 'needs_update') {
      statusColor = Colors.red;
      statusText = '업데이트 필요';
    } else if (status == 'archived') {
      statusColor = Colors.grey;
      statusText = '보관됨';
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(Icons.description_outlined,
                color: statusColor, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(diagnosis,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 14)),
                Text(formattedDate,
                    style:
                        const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              statusText,
              style: TextStyle(
                  color: statusColor,
                  fontSize: 11,
                  fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPendingOcrCard() {
    final jobs =
        (_data?['pending_ocr_jobs'] as List?)?.cast<Map<String, dynamic>>() ??
            [];

    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(
            'OCR 처리 내역',
            Icons.document_scanner_outlined,
            onMore: _openOcrHistory,
          ),
          const SizedBox(height: 12),
          if (jobs.isEmpty)
            const Text('처리 중인 문서가 없습니다.',
                style: TextStyle(color: Colors.grey, fontSize: 14))
          else
            ...jobs.map((j) => _buildOcrJobItem(j)),
        ],
      ),
    );
  }

  Widget _buildOcrJobItem(Map<String, dynamic> job) {
    final filename = job['original_filename'] as String? ?? '문서';
    final status = job['ocr_status'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          const Icon(Icons.insert_drive_file_outlined,
              color: Colors.grey, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(filename,
                style: const TextStyle(fontSize: 14),
                overflow: TextOverflow.ellipsis),
          ),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.orange.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              status == 'processing' ? '처리 중' : '대기 중',
              style: const TextStyle(
                  color: Colors.orange,
                  fontSize: 11,
                  fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}