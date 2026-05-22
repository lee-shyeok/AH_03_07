import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';
import 'home_page.dart';

class OcrHistoryPage extends StatefulWidget {
  const OcrHistoryPage({super.key});

  @override
  State<OcrHistoryPage> createState() => _OcrHistoryPageState();
}

class _OcrHistoryPageState extends State<OcrHistoryPage> {
  final _client = http.Client();
  bool _isLoading = true;
  bool _hasError = false;
  List<Map<String, dynamic>> _documents = [];

  @override
  void initState() {
    super.initState();
    _loadDocuments();
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
                pageBuilder: (_, __, ___) => const HomePage(),
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

  Future<void> _loadDocuments() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _documents =
              List<Map<String, dynamic>>.from(data['items'] ?? []);
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

  Future<void> _deleteDocument(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('문서 삭제',
            style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('이 의료문서를 삭제하시겠습니까?'),
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
        Uri.parse('${OcrConfig.baseUrl}/v1/medical-documents/$id'),
        headers: {'Authorization': 'Bearer $token'},
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 204) {
        setState(() => _documents.removeWhere((d) => d['id'] == id));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('문서가 삭제됐습니다.')),
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

  String _getDocumentTypeLabel(String? type) {
    const labels = {
      'prescription': '처방전',
      'medical_record': '진료기록',
      'pill_bag': '약봉투',
      'lab_result': '검사결과지',
      'health_checkup': '건강검진',
      'other': '기타',
    };
    return labels[type] ?? '기타';
  }

  Color _getDocumentTypeColor(String? type) {
    const colors = {
      'prescription': Color(0xFFFF8C00),
      'medical_record': Color(0xFF4CAF50),
      'pill_bag': Color(0xFF2196F3),
      'lab_result': Color(0xFF9C27B0),
      'health_checkup': Color(0xFFFF5722),
      'other': Color(0xFF607D8B),
    };
    return colors[type] ?? const Color(0xFF607D8B);
  }

  IconData _getDocumentTypeIcon(String? type) {
    const icons = {
      'prescription': Icons.receipt_long_outlined,
      'medical_record': Icons.medical_services_outlined,
      'pill_bag': Icons.medication_outlined,
      'lab_result': Icons.science_outlined,
      'health_checkup': Icons.health_and_safety_outlined,
      'other': Icons.description_outlined,
    };
    return icons[type] ?? Icons.description_outlined;
  }

  String _getStatusLabel(String? status) {
    const labels = {
      'uploaded': '업로드됨',
      'confirmed': '확정됨',
      'deleted': '삭제됨',
    };
    return labels[status] ?? status ?? '';
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'confirmed':
        return Colors.green;
      case 'uploaded':
        return Colors.orange;
      default:
        return Colors.grey;
    }
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
          'OCR 처리 내역',
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
              child: CircularProgressIndicator(color: Color(0xFFFF8C00)))
          : _hasError
              ? _buildError()
              : RefreshIndicator(
                  color: const Color(0xFFFF8C00),
                  onRefresh: _loadDocuments,
                  child: _documents.isEmpty
                      ? _buildEmpty()
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _documents.length,
                          itemBuilder: (_, i) =>
                              _buildDocumentCard(_documents[i]),
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
            onPressed: _loadDocuments,
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
          Icon(Icons.document_scanner_outlined,
              size: 64, color: Colors.grey.shade300),
          const SizedBox(height: 16),
          const Text('OCR 처리 내역이 없습니다.',
              style: TextStyle(color: Colors.grey, fontSize: 16)),
          const SizedBox(height: 8),
          const Text('의료문서를 업로드하면 여기에 표시됩니다.',
              style: TextStyle(color: Colors.grey, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildDocumentCard(Map<String, dynamic> doc) {
    final id = doc['id'] as int? ?? 0;
    final docType = doc['document_type'] as String?;
    final filename = doc['original_filename'] as String? ?? '파일명 없음';
    final status = doc['upload_status'] as String?;
    final isConfirmed = doc['is_user_confirmed'] as bool? ?? false;
    final createdAt = doc['created_at'] as String? ?? '';
    final fileSize = doc['file_size'] as int?;

    String formattedDate = createdAt;
    try {
      final dt = DateTime.parse(createdAt).toLocal();
      formattedDate =
          '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')} '
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {}

    String fileSizeText = '';
    if (fileSize != null) {
      if (fileSize < 1024) {
        fileSizeText = '${fileSize}B';
      } else if (fileSize < 1024 * 1024) {
        fileSizeText = '${(fileSize / 1024).toStringAsFixed(1)}KB';
      } else {
        fileSizeText =
            '${(fileSize / (1024 * 1024)).toStringAsFixed(1)}MB';
      }
    }

    final typeColor = _getDocumentTypeColor(docType);
    final typeIcon = _getDocumentTypeIcon(docType);
    final typeLabel = _getDocumentTypeLabel(docType);

    return Container(
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
              color: typeColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(typeIcon, color: typeColor, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: typeColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        typeLabel,
                        style: TextStyle(
                          fontSize: 11,
                          color: typeColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: _getStatusColor(status).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        isConfirmed ? '확정됨' : _getStatusLabel(status),
                        style: TextStyle(
                          fontSize: 11,
                          color: _getStatusColor(status),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  filename,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: Colors.black87,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  fileSizeText.isNotEmpty
                      ? '$formattedDate · $fileSizeText'
                      : formattedDate,
                  style: const TextStyle(
                      color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.delete_outline,
                color: Colors.grey.shade400, size: 20),
            onPressed: () => _deleteDocument(id),
          ),
        ],
      ),
    );
  }
}