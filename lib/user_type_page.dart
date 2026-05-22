import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'main.dart';
import 'login_page.dart';
import 'home_page.dart';

class UserTypePage extends StatefulWidget {
  const UserTypePage({super.key});

  @override
  State<UserTypePage> createState() => _UserTypePageState();
}

class _UserTypePageState extends State<UserTypePage> {
  final _storage = const FlutterSecureStorage();
  String? _selectedType;
  bool _isLoading = false;

  static const _green = Color(0xFF2ECC71);
  static const _purple = Color(0xFF7C5CCF);

  void _navigateToMain() {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => const HomePage(),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
        transitionDuration: const Duration(milliseconds: 400),
      ),
    );
  }

  Future<void> _confirm() async {
    if (_selectedType == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('사용 유형을 선택해주세요.')),
      );
      return;
    }
    if (_isLoading) return;
    setState(() => _isLoading = true);
    try {
      await _storage.write(key: 'user_type', value: _selectedType);
      if (!mounted) return;
      _navigateToMain();
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _skipForNow() async {
    await _storage.write(key: 'user_type', value: 'general');
    if (!mounted) return;
    _navigateToMain();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),
              IconButton(
                icon: const Icon(Icons.chevron_left,
                    color: Colors.black87, size: 28),
                onPressed: () => Navigator.pop(context),
                padding: EdgeInsets.zero,
              ),
              const SizedBox(height: 24),
              const Text(
                '어떤 도움이\n필요하신가요?',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                '맞춤 가이드를 제공해드릴게요',
                style: TextStyle(fontSize: 14, color: Colors.grey),
              ),
              const SizedBox(height: 40),

              // ── 일반 환자 ──
              _buildTypeCard(
                key: 'general',
                title: '일반 환자',
                lines: ['복약 관리', '일반 의료 정보'],
                color: _green,
                emoji: '🟢',
              ),
              const SizedBox(height: 16),

              // ── 자가면역환자 ──
              _buildTypeCard(
                key: 'autoimmune',
                title: '자가면역환자',
                lines: ['활성도 추적', '면역약물 특화 정보'],
                color: _purple,
                emoji: '🟣',
              ),

              const Spacer(),

              // ── 확인 버튼 ──
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _confirm,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _selectedType == 'general'
                        ? _green
                        : _selectedType == 'autoimmune'
                            ? _purple
                            : Colors.grey.shade300,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    elevation: 0,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : const Text(
                          '확인',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                ),
              ),
              const SizedBox(height: 16),

              // ── 나중에 선택 ──
              Center(
                child: GestureDetector(
                  onTap: _skipForNow,
                  child: const Text(
                    '나중에 선택할게요',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTypeCard({
    required String key,
    required String title,
    required List<String> lines,
    required Color color,
    required String emoji,
  }) {
    final isSelected = _selectedType == key;
    return Semantics(
      label: '$title 선택',
      selected: isSelected,
      child: GestureDetector(
        onTap: () {
          HapticFeedback.selectionClick();
          setState(() => _selectedType = key);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: isSelected ? color.withOpacity(0.05) : Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? color : Colors.grey.shade200,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: isSelected
                      ? color.withOpacity(0.12)
                      : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(26),
                ),
                child: Center(
                  child: Text(emoji, style: const TextStyle(fontSize: 24)),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: isSelected ? color : Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    ...lines.map((line) => Text(
                          line,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade600,
                            height: 1.5,
                          ),
                        )),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right,
                  color: Colors.grey, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}