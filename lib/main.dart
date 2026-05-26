import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'services/auth_service.dart';
import 'services/ocr_service.dart';
import 'login_page.dart';
import 'splash_screen.dart';
import 'home_page.dart';

class SecureTokenStorage implements TokenStorage {
  final _storage = const FlutterSecureStorage(
    webOptions: WebOptions(
      dbName: 'medapp_storage',
      publicKey: 'medapp_key',
    ),
  );

  @override
  Future<String?> getAccessToken() => _storage.read(key: 'access_token');

  @override
  Future<String?> getRefreshToken() => _storage.read(key: 'refresh_token');

  @override
  Future<void> saveAccessToken(String token) =>
      _storage.write(key: 'access_token', value: token);

  @override
  Future<void> saveRefreshToken(String token) =>
      _storage.write(key: 'refresh_token', value: token);

  @override
  Future<void> saveUserId(String id) =>
      _storage.write(key: 'user_id', value: id);

  @override
  Future<void> saveUserEmail(String email) =>
      _storage.write(key: 'user_email', value: email);

  @override
  Future<void> deleteAll() => _storage.deleteAll();
}

enum OcrStatus { idle, uploading, processing, done, confirmed, error }

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '의료문서 OCR',
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('ko', 'KR'),
      ],
      locale: const Locale('ko', 'KR'),
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFFF8C00)),
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}

class MainPage extends StatelessWidget {
  const MainPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const HomePage();
  }
}

class OcrPage extends StatefulWidget {
  final Future<void> Function() onLogout;
  const OcrPage({super.key, required this.onLogout});

  @override
  State<OcrPage> createState() => _OcrPageState();
}

class _OcrPageState extends State<OcrPage> {
  late final OcrService _ocrService;
  final ImagePicker _picker = ImagePicker();

  XFile? _selectedFile;
  OcrStatus _status = OcrStatus.idle;
  String _statusMessage = '';
  Map<String, dynamic>? _ocrResult;
  String? _documentId;

  bool get _isLoading =>
      _status == OcrStatus.uploading || _status == OcrStatus.processing;

  @override
  void initState() {
    super.initState();
    _ocrService = OcrService(tokenStorage: SecureTokenStorage());
  }

  @override
  void dispose() {
    _ocrService.dispose();
    super.dispose();
  }

  void _setStatus(OcrStatus status, String message) {
    if (mounted) {
      setState(() {
        _status = status;
        _statusMessage = message;
      });
    }
  }

  Future<File> _writeTempFile(String name, List<int> bytes) async {
    final dir = Directory.systemTemp;
    final file = File('${dir.path}/$name');
    await file.writeAsBytes(bytes);
    return file;
  }

  Future<void> _pickAndProcess(ImageSource source) async {
    final picked = await _picker.pickImage(source: source);
    if (picked == null) return;

    setState(() {
      _selectedFile = picked;
      _ocrResult = null;
    });

    _setStatus(OcrStatus.uploading, '문서 업로드 중...');

    try {
      final bytes = await picked.readAsBytes();
      final tempFile = await _writeTempFile(picked.name, bytes);

      _documentId = await _ocrService.uploadDocument(tempFile, 'prescription');
      _setStatus(OcrStatus.processing, 'OCR 처리 중...');

      final jobId = await _ocrService.startOcrJob(_documentId!);
      final result = await _ocrService.getOcrResult(jobId);

      if (mounted) {
        setState(() {
          _ocrResult = result;
          _status = OcrStatus.done;
          _statusMessage = 'OCR 완료! 결과를 확인하고 확정하세요.';
        });
      }
    } on AuthException catch (e) {
      _setStatus(OcrStatus.error, '인증 오류: ${e.message}');
    } on OcrException catch (e) {
      _setStatus(OcrStatus.error, '오류: ${e.message}');
    } on NetworkException catch (e) {
      _setStatus(OcrStatus.error, '네트워크 오류: ${e.message}');
    } catch (_) {
      _setStatus(OcrStatus.error, '알 수 없는 오류가 발생했습니다.');
    }
  }

  Future<void> _confirm() async {
    if (_documentId == null || _ocrResult == null) return;

    _setStatus(OcrStatus.uploading, '확정 중...');

    try {
      await _ocrService.confirmOcrResult(
        _documentId!,
        _ocrResult!['structured_data'] ?? {},
      );
      _setStatus(OcrStatus.confirmed, '✅ 확정 완료!');
    } on AuthException catch (e) {
      _setStatus(OcrStatus.error, '인증 오류: ${e.message}');
    } on OcrException catch (e) {
      _setStatus(OcrStatus.error, '오류: ${e.message}');
    } on NetworkException catch (e) {
      _setStatus(OcrStatus.error, '네트워크 오류: ${e.message}');
    } catch (_) {
      _setStatus(OcrStatus.error, '알 수 없는 오류가 발생했습니다.');
    }
  }

  Color get _statusColor {
    switch (_status) {
      case OcrStatus.error:
        return Colors.red;
      case OcrStatus.confirmed:
        return Colors.green;
      default:
        return Colors.black87;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('의료문서 OCR'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: '로그아웃',
            onPressed: _isLoading ? null : widget.onLogout,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _isLoading
                      ? null
                      : () => _pickAndProcess(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('카메라'),
                ),
                ElevatedButton.icon(
                  onPressed: _isLoading
                      ? null
                      : () => _pickAndProcess(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('갤러리'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (_selectedFile != null)
              FutureBuilder<Uint8List>(
                future: _selectedFile!.readAsBytes(),
                builder: (context, snapshot) {
                  if (!snapshot.hasData) return const SizedBox.shrink();
                  return ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.memory(
                      snapshot.data!,
                      height: 200,
                      fit: BoxFit.cover,
                    ),
                  );
                },
              ),
            const SizedBox(height: 16),
            if (_statusMessage.isNotEmpty)
              Text(
                _statusMessage,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: _statusColor,
                ),
              ),
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.only(top: 16),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (_status == OcrStatus.done && _ocrResult != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.grey.shade50,
                ),
                child: SelectableText(
                  _ocrResult!['structured_data']?['raw_text'] ?? '텍스트 없음',
                  style: const TextStyle(fontSize: 14),
                ),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _confirm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFF8C00),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text(
                  '확정하기',
                  style: TextStyle(color: Colors.white, fontSize: 16),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}