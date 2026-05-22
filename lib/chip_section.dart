import 'package:flutter/material.dart';
import 'services/user_service.dart';
import 'services/ocr_service.dart';

class ChipSection extends StatefulWidget {
  final TokenStorage tokenStorage;
  final List<String> initialItems;
  final String hint;
  final String saveKey;

  const ChipSection({
    super.key,
    required this.tokenStorage,
    required this.initialItems,
    required this.hint,
    required this.saveKey,
  });

  @override
  State<ChipSection> createState() => _ChipSectionState();
}

class _ChipSectionState extends State<ChipSection> {
  late List<String> _items;
  late final UserService _userService;
  final _controller = TextEditingController();
  bool _saving = false;

  static const _green = Color(0xFF2ECC71);
  static const _cardBg = Colors.white;
  static const _textSecondary = Color(0xFF888888);

  @override
  void initState() {
    super.initState();
    _items = List.from(widget.initialItems);
    _userService = UserService(tokenStorage: widget.tokenStorage);
  }

  @override
  void dispose() {
    _controller.dispose();
    _userService.dispose();
    super.dispose();
  }

  void _add() {
    final v = _controller.text.trim();
    if (v.isNotEmpty && !_items.contains(v)) {
      setState(() {
        _items.add(v);
        _controller.clear();
      });
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      // 백엔드가 string 타입이므로 쉼표로 이어붙여서 전송
      await _userService.patchMe({widget.saveKey: _items.join(', ')});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('저장됐습니다.'),
          backgroundColor: _green,
        ));
      }
    } on AuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(e.message),
          backgroundColor: Colors.red,
        ));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('저장 중 오류가 발생했습니다.'),
          backgroundColor: Colors.red,
        ));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  hintText: widget.hint,
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 12),
                ),
                onSubmitted: (_) => _add(),
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              height: 48,
              child: ElevatedButton(
                onPressed: _add,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _green,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                ),
                child: const Text('추가',
                    style: TextStyle(color: Colors.white)),
              ),
            ),
          ]),
          if (_items.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: _items
                  .map((item) => Chip(
                        label: Text(item,
                            style: const TextStyle(fontSize: 13)),
                        deleteIcon: const Icon(Icons.close, size: 16),
                        onDeleted: () =>
                            setState(() => _items.remove(item)),
                        backgroundColor: const Color(0xFFE8F8F0),
                        deleteIconColor: _textSecondary,
                        side: BorderSide.none,
                      ))
                  .toList(),
            ),
          ],
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 46,
            child: ElevatedButton(
              onPressed: _saving ? null : _save,
              style: ElevatedButton.styleFrom(
                backgroundColor: _green,
                disabledBackgroundColor: _green.withOpacity(0.5),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                elevation: 0,
              ),
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2.5))
                  : const Text('저장',
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }
}