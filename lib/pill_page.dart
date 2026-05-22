import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';
import 'services/ocr_service.dart';
import 'main.dart';
import 'login_page.dart';
import 'home_page.dart';

// ── 약품 이미지 업로드 (REQ-PILL-001) ────────────────────
class PillRecognizePage extends StatefulWidget {
  const PillRecognizePage({super.key});

  @override
  State<PillRecognizePage> createState() => _PillRecognizePageState();
}

class _PillRecognizePageState extends State<PillRecognizePage> {
  final _client = http.Client();
  bool _isUploading = false;
  XFile? _selectedImage;
  List<Map<String, dynamic>> _candidates = [];
  bool _showResult = false;

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

  Future<void> _pickImage(ImageSource source) async {
    try {
      final picker = ImagePicker();
      final image = await picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );
      if (image != null) {
        setState(() {
          _selectedImage = image;
          _showResult = false;
          _candidates = [];
        });
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('이미지를 불러오지 못했습니다.')),
      );
    }
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('이미지 선택',
                style: TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined,
                  color: Color(0xFFFF8C00)),
              title: const Text('카메라로 촬영'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined,
                  color: Color(0xFFFF8C00)),
              title: const Text('갤러리에서 선택'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _recognizePill() async {
    if (_selectedImage == null) return;
    setState(() => _isUploading = true);

    try {
      final token = await _getToken();
      if (token == null) throw Exception('토큰 없음');

      final bytes = await _selectedImage!.readAsBytes();
      final filename = _selectedImage!.name;
      final ext = filename.split('.').last.toLowerCase();
      final mimeType = ext == 'png' ? 'image/png' : 'image/jpeg';

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${OcrConfig.baseUrl}/v1/pills/recognize'),
      );
      request.headers['Authorization'] = 'Bearer $token';
      request.files.add(http.MultipartFile.fromBytes(
        'image',
        bytes,
        filename: filename,
        contentType: MediaType.parse(mimeType),
      ));

      final streamedResponse = await request.send()
          .timeout(const Duration(seconds: 60));
      final response = await http.Response.fromStream(streamedResponse);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _candidates = List<Map<String, dynamic>>.from(
              data['candidates'] ?? []);
          _showResult = true;
          _isUploading = false;
        });
      } else if (response.statusCode == 401) {
        _handleUnauthorized();
      } else {
        setState(() => _isUploading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('약품 인식에 실패했습니다.')),
        );
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => _isUploading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('오류가 발생했습니다.')),
      );
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
          '약품 이미지 인식',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (_) => const PillHistoryPage()),
            ),
            child: const Text('인식 내역',
                style: TextStyle(color: Color(0xFFFF8C00))),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 안내 문구
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFFF8C00).withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: const Color(0xFFFF8C00).withOpacity(0.2)),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline,
                      color: Color(0xFFFF8C00), size: 18),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '약품 이미지를 촬영하거나 선택하면 후보 약품을 제시합니다. 최종 확정은 사용자가 직접 해주세요.',
                      style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                          height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // 이미지 선택 영역
            GestureDetector(
              onTap: _showImageSourceDialog,
              child: Container(
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _selectedImage != null
                        ? const Color(0xFFFF8C00)
                        : Colors.grey.shade300,
                    width: _selectedImage != null ? 2 : 1,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: _selectedImage == null
                    ? Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.add_photo_alternate_outlined,
                              size: 48,
                              color: Colors.grey.shade400),
                          const SizedBox(height: 12),
                          const Text('탭하여 약품 이미지 선택',
                              style: TextStyle(
                                  color: Colors.grey, fontSize: 14)),
                        ],
                      )
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child: FutureBuilder<Uint8List>(
                          future: _selectedImage!.readAsBytes(),
                          builder: (context, snapshot) {
                            if (snapshot.hasData) {
                              return Image.memory(
                                snapshot.data!,
                                fit: BoxFit.cover,
                                width: double.infinity,
                              );
                            }
                            return const Center(
                              child: CircularProgressIndicator(
                                  color: Color(0xFFFF8C00)),
                            );
                          },
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 16),

            // 인식 버튼
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: (_selectedImage == null || _isUploading)
                    ? null
                    : _recognizePill,
                icon: _isUploading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.search, color: Colors.white),
                label: Text(
                  _isUploading ? '인식 중...' : '약품 인식 시작',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFF8C00),
                  disabledBackgroundColor: Colors.grey.shade300,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
              ),
            ),

            // 인식 결과
            if (_showResult) ...[
              const SizedBox(height: 24),
              const Text(
                '인식 결과',
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87),
              ),
              const SizedBox(height: 8),
              if (_candidates.isEmpty)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text('인식된 약품이 없습니다.',
                      style: TextStyle(color: Colors.grey)),
                )
              else
                ...(_candidates.map((c) => _buildCandidateCard(c))),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                  border:
                      Border.all(color: Colors.orange.withOpacity(0.2)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.warning_amber_outlined,
                        color: Colors.orange, size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '위 결과는 참고용입니다. 반드시 직접 확인 후 사용하세요.',
                        style: TextStyle(
                            fontSize: 12,
                            color: Colors.orange,
                            height: 1.4),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCandidateCard(Map<String, dynamic> candidate) {
    final drugName = candidate['drug_name'] as String? ?? '';
    final confidence = (candidate['confidence'] as num?)?.toDouble() ?? 0.0;
    final confidencePercent = (confidence * 100).toStringAsFixed(1);

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
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFFFF8C00).withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.medication_outlined,
                color: Color(0xFFFF8C00), size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(drugName,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Colors.black87)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Text('일치도: ',
                        style:
                            TextStyle(color: Colors.grey, fontSize: 12)),
                    Text(
                      '$confidencePercent%',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: confidence >= 0.8
                            ? Colors.green
                            : confidence >= 0.6
                                ? Colors.orange
                                : Colors.red,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          // 일치도 바
          SizedBox(
            width: 60,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: confidence,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation<Color>(
                  confidence >= 0.8
                      ? Colors.green
                      : confidence >= 0.6
                          ? Colors.orange
                          : Colors.red,
                ),
                minHeight: 6,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 약품 인식 내역 (REQ-PILL-004) ─────────────────────────
class PillHistoryPage extends StatefulWidget {
  const PillHistoryPage({super.key});

  @override
  State<PillHistoryPage> createState() => _PillHistoryPageState();
}

class _PillHistoryPageState extends State<PillHistoryPage> {
  final _client = http.Client();
  bool _isLoading = true;
  bool _hasError = false;
  List<Map<String, dynamic>> _recognitions = [];

  @override
  void initState() {
    super.initState();
    _loadRecognitions();
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<void> _loadRecognitions() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
    });

    try {
      final token = await SecureTokenStorage().getAccessToken();
      if (token == null) throw Exception('토큰 없음');

      final response = await _client.get(
        Uri.parse('${OcrConfig.baseUrl}/v1/pills/recognitions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(OcrConfig.timeoutDuration);

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _recognitions = List<Map<String, dynamic>>.from(
              data is List ? data : data['items'] ?? []);
          _isLoading = false;
        });
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
          '약품 인식 내역',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFFFF8C00)))
          : _hasError
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text('데이터를 불러오지 못했습니다.',
                          style: TextStyle(color: Colors.grey)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadRecognitions,
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
                )
              : RefreshIndicator(
                  color: const Color(0xFFFF8C00),
                  onRefresh: _loadRecognitions,
                  child: _recognitions.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.medication_outlined,
                                  size: 64,
                                  color: Colors.grey.shade300),
                              const SizedBox(height: 16),
                              const Text('약품 인식 내역이 없습니다.',
                                  style: TextStyle(
                                      color: Colors.grey,
                                      fontSize: 16)),
                            ],
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _recognitions.length,
                          itemBuilder: (_, i) =>
                              _buildRecognitionCard(_recognitions[i]),
                        ),
                ),
    );
  }

  Widget _buildRecognitionCard(Map<String, dynamic> recognition) {
    final candidates = (recognition['candidates'] as List?)
            ?.cast<Map<String, dynamic>>() ??
        [];
    final createdAt = recognition['created_at'] as String? ?? '';
    final topCandidate = candidates.isNotEmpty ? candidates.first : null;

    String formattedDate = createdAt;
    try {
      final dt = DateTime.parse(createdAt).toLocal();
      formattedDate =
          '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')} '
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {}

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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xFFFF8C00).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.medication_outlined,
                    color: Color(0xFFFF8C00), size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      topCandidate != null
                          ? topCandidate['drug_name'] as String? ?? '약품명 없음'
                          : '인식 결과 없음',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          color: Colors.black87),
                    ),
                    Text(formattedDate,
                        style: const TextStyle(
                            color: Colors.grey, fontSize: 12)),
                  ],
                ),
              ),
              Text(
                '후보 ${candidates.length}개',
                style: const TextStyle(
                    color: Color(0xFFFF8C00),
                    fontSize: 12,
                    fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
