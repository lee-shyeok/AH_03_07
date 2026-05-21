import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';

class MedicalRecordsPage extends StatefulWidget {
  const MedicalRecordsPage({super.key});

  @override
  State<MedicalRecordsPage> createState() => _MedicalRecordsPageState();
}

class _MedicalRecordsPageState extends State<MedicalRecordsPage> {
  bool _isLoading = true;
  bool _hasError = false;
  List<Map<String, dynamic>> _records = [];
  final _client = http.Client();

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<String?> _getToken() async {
    return SecureTokenStorage().getAccessToken();
  }

  Future<void> _loadRecords() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-records'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _records = (data['items'] as List).cast<Map<String, dynamic>>();
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

  Future<void> _deleteRecord(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('진료기록 삭제'),
        content: const Text('이 진료기록을 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      final token = await _getToken();
      if (token == null) return;

      final response = await _client.delete(
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-records/$id'),
        headers: {'Authorization': 'Bearer $token'},
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 204) {
        setState(() => _records.removeWhere((r) => r['id'] == id));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('진료기록이 삭제됐습니다.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('삭제에 실패했습니다.')),
        );
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('오류가 발생했습니다.')),
      );
    }
  }

  void _openAddRecord() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => const MedicalRecordFormPage(),
      ),
    ).then((_) => _loadRecords());
  }

  void _openDetail(Map<String, dynamic> record) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => MedicalRecordDetailPage(record: record),
      ),
    ).then((_) => _loadRecords());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          '진료기록',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        centerTitle: false,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _openAddRecord,
        backgroundColor: const Color(0xFFFF8C00),
        tooltip: '진료기록 추가',
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFFFF8C00)))
          : _hasError
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadRecords,
                  color: const Color(0xFFFF8C00),
                  child: _records.isEmpty
                      ? _buildEmpty()
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _records.length,
                          itemBuilder: (_, i) =>
                              _buildRecordCard(_records[i]),
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
              style: TextStyle(color: Colors.grey)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadRecords,
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

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.medical_services_outlined,
              size: 64, color: Colors.grey.shade300),
          const SizedBox(height: 16),
          const Text('진료기록이 없습니다.',
              style: TextStyle(color: Colors.grey, fontSize: 16)),
          const SizedBox(height: 8),
          const Text('+ 버튼을 눌러 진료기록을 추가하세요.',
              style: TextStyle(color: Colors.grey, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildRecordCard(Map<String, dynamic> record) {
    final id = record['id'] as int? ?? 0;
    final visitDate = record['visit_date'] as String? ?? '';
    final hospitalName = record['hospital_name'] as String? ?? '병원명 없음';
    final diagnosis = record['diagnosis'] as String? ?? '';
    final medicationCount = record['medication_count'] as int? ?? 0;

    String formattedDate = visitDate;
    try {
      final date = DateTime.parse(visitDate);
      formattedDate = DateFormat('yyyy년 MM월 dd일').format(date);
    } catch (_) {}

    return Semantics(
      label: '$hospitalName 진료기록',
      child: GestureDetector(
        onTap: () => _openDetail(record),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
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
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: const Color(0xFFFF8C00).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.local_hospital_outlined,
                  color: Color(0xFFFF8C00),
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      hospitalName,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      diagnosis,
                      style: const TextStyle(
                          color: Colors.grey, fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$formattedDate · 약 $medicationCount종',
                      style: const TextStyle(
                          color: Colors.grey, fontSize: 12),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline,
                    color: Colors.grey, size: 20),
                onPressed: () => _deleteRecord(id),
                tooltip: '삭제',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── 진료기록 상세 ──────────────────────────────────────
class MedicalRecordDetailPage extends StatelessWidget {
  final Map<String, dynamic> record;
  const MedicalRecordDetailPage({super.key, required this.record});

  @override
  Widget build(BuildContext context) {
    final visitDate = record['visit_date'] as String? ?? '';
    final hospitalName = record['hospital_name'] as String? ?? '병원명 없음';
    final diagnosis = record['diagnosis'] as String? ?? '';
    final memo = record['memo'] as String? ?? '';
    final medications = (record['medications'] as List?)
            ?.cast<Map<String, dynamic>>() ??
        [];

    String formattedDate = visitDate;
    try {
      formattedDate =
          DateFormat('yyyy년 MM월 dd일').format(DateTime.parse(visitDate));
    } catch (_) {}

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          '진료기록 상세',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDetailCard('기본 정보', [
              _buildDetailRow('병원명', hospitalName),
              _buildDetailRow('진료일', formattedDate),
              _buildDetailRow('진단명', diagnosis),
            ]),
            if (memo.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildDetailCard('메모', [
                Text(memo,
                    style: const TextStyle(
                        fontSize: 14, color: Colors.black87, height: 1.6)),
              ]),
            ],
            if (medications.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildDetailCard(
                '처방 약품',
                medications.map((m) => _buildMedicationRow(m)).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetailCard(String title, List<Widget> children) {
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87)),
          const Divider(height: 20),
          ...children,
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(label,
                style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicationRow(Map<String, dynamic> med) {
    final name = med['drug_name'] as String? ?? '';
    final dosage = med['dosage'] as String? ?? '';
    final frequency = med['frequency'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: const Color(0xFFFF8C00).withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.medication_outlined,
                color: Color(0xFFFF8C00), size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 14)),
                Text('$dosage · $frequency',
                    style: const TextStyle(
                        color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── 진료기록 직접 입력 ────────────────────────────────
class MedicalRecordFormPage extends StatefulWidget {
  final Map<String, dynamic>? record;
  const MedicalRecordFormPage({super.key, this.record});

  @override
  State<MedicalRecordFormPage> createState() =>
      _MedicalRecordFormPageState();
}

class _MedicalRecordFormPageState extends State<MedicalRecordFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _hospitalController = TextEditingController();
  final _diagnosisController = TextEditingController();
  final _memoController = TextEditingController();
  DateTime? _visitDate;
  bool _isLoading = false;
  final _client = http.Client();

  @override
  void initState() {
    super.initState();
    if (widget.record != null) {
      _hospitalController.text =
          widget.record!['hospital_name'] as String? ?? '';
      _diagnosisController.text =
          widget.record!['diagnosis'] as String? ?? '';
      _memoController.text = widget.record!['memo'] as String? ?? '';
      try {
        _visitDate =
            DateTime.parse(widget.record!['visit_date'] as String? ?? '');
      } catch (_) {}
    }
  }

  @override
  void dispose() {
    _hospitalController.dispose();
    _diagnosisController.dispose();
    _memoController.dispose();
    _client.close();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
      locale: const Locale('ko', 'KR'),
    );
    if (picked != null && mounted) {
      setState(() => _visitDate = picked);
    }
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (_visitDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('진료일을 선택해주세요.')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final token = await SecureTokenStorage().getAccessToken();
      if (token == null) return;

      final isEdit = widget.record != null;
      final id = widget.record?['id'] as int?;

      final body = jsonEncode({
        'visit_date': DateFormat('yyyy-MM-dd').format(_visitDate!),
        'hospital_name': _hospitalController.text.trim(),
        'diagnosis': _diagnosisController.text.trim(),
        'memo': _memoController.text.trim(),
        'medications': [],
      });

      final uri = isEdit
          ? Uri.parse('${OcrConfig.baseUrl}/v1/medical-records/$id')
          : Uri.parse('${OcrConfig.baseUrl}/v1/medical-records');

      final response = isEdit
          ? await _client.patch(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
              body: body,
            ).timeout(OcrConfig.timeoutDuration)
          : await _client.post(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
              body: body,
            ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content:
                  Text(isEdit ? '진료기록이 수정됐습니다.' : '진료기록이 추가됐습니다.')),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('저장에 실패했습니다.')),
        );
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('오류가 발생했습니다.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.record != null;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          isEdit ? '진료기록 수정' : '진료기록 추가',
          style: const TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              GestureDetector(
                onTap: _pickDate,
                child: AbsorbPointer(
                  child: TextFormField(
                    controller: TextEditingController(
                      text: _visitDate == null
                          ? ''
                          : DateFormat('yyyy년 MM월 dd일').format(_visitDate!),
                    ),
                    decoration: const InputDecoration(
                      labelText: '진료일 *',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.calendar_today_outlined),
                      hintText: '날짜 선택',
                    ),
                    validator: (_) =>
                        _visitDate == null ? '진료일을 선택해주세요.' : null,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _hospitalController,
                decoration: const InputDecoration(
                  labelText: '병원명',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.local_hospital_outlined),
                ),
                validator: (v) => v == null || v.trim().isEmpty
                    ? '병원명을 입력해주세요.'
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _diagnosisController,
                decoration: const InputDecoration(
                  labelText: '진단명 *',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.medical_services_outlined),
                ),
                validator: (v) => v == null || v.trim().isEmpty
                    ? '진단명을 입력해주세요.'
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _memoController,
                decoration: const InputDecoration(
                  labelText: '메모',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.note_outlined),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 32),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFF8C00),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                    elevation: 0,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : Text(
                          isEdit ? '수정하기' : '저장하기',
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}