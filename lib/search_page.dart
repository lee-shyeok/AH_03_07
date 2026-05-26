import 'package:flutter/material.dart';
import 'medical_records_page.dart';
import 'guides_page.dart';

// ════════════════════════════════════════════════════════════
// 검색 화면
// ════════════════════════════════════════════════════════════

class SearchPage extends StatefulWidget {
  const SearchPage({super.key});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final _searchController = TextEditingController();
  final _focusNode = FocusNode();
  List<String> _recentSearches = [
    '메토트렉세이트',
    '활성도 기록 방법',
    '비염',
    '면역억제제 부작용',
  ];

  static const _popularSearches = [
    '통증', '관절통', '활성도', '수면', '복약 시간', '메토트렉세이드'
  ];

  static const _bg = Color(0xFFF8FAF8);
  static const _cardBg = Colors.white;
  static const _textPrimary = Color(0xFF1A1A1A);
  static const _textSecondary = Color(0xFF888888);
  static const _divider = Color(0xFFF0F0F0);
  static const _green = Color(0xFF2ECC71);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _search(String query) {
    final q = query.trim();
    if (q.isEmpty) return;
    setState(() {
      _recentSearches.remove(q);
      _recentSearches.insert(0, q);
      if (_recentSearches.length > 10) {
        _recentSearches = _recentSearches.sublist(0, 10);
      }
    });
    _searchController.text = q;
    _focusNode.unfocus();
    debugPrint('Search: $q');
  }

  void _removeRecent(String query) {
    setState(() => _recentSearches.remove(query));
  }

  void _navigateCategory(String route) {
    switch (route) {
      case 'medical_records':
        Navigator.push(context,
            MaterialPageRoute(builder: (_) => const MedicalRecordsPage()));
        break;
      case 'guides':
        Navigator.push(context,
            MaterialPageRoute(builder: (_) => const GuidesPage()));
        break;
      default:
        debugPrint('Navigate to: $route');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: SafeArea(
        child: Column(
          children: [
            // ── 검색바 ──
            Container(
              color: _cardBg,
              padding: const EdgeInsets.fromLTRB(8, 8, 16, 8),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.chevron_left,
                        color: _textPrimary, size: 28),
                    onPressed: () => Navigator.pop(context),
                  ),
                  Expanded(
                    child: Container(
                      height: 44,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF5F5F5),
                        borderRadius: BorderRadius.circular(22),
                      ),
                      child: TextField(
                        controller: _searchController,
                        focusNode: _focusNode,
                        decoration: const InputDecoration(
                          hintText: '검색...',
                          hintStyle: TextStyle(
                              color: _textSecondary, fontSize: 14),
                          prefixIcon: Icon(Icons.search,
                              color: _textSecondary, size: 20),
                          border: InputBorder.none,
                          contentPadding:
                              EdgeInsets.symmetric(vertical: 12),
                        ),
                        textInputAction: TextInputAction.search,
                        onSubmitted: _search,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ── 내용 ──
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── 최근 검색어 ──
                    if (_recentSearches.isNotEmpty) ...[
                      const Text('최근 검색어',
                          style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: _textSecondary)),
                      const SizedBox(height: 10),
                      Container(
                        decoration: BoxDecoration(
                          color: _cardBg,
                          borderRadius: BorderRadius.circular(14),
                          border:
                              Border.all(color: const Color(0xFFE8E8E8)),
                        ),
                        child: Column(
                          children: List.generate(
                              _recentSearches.length, (i) {
                            final query = _recentSearches[i];
                            return Column(
                              children: [
                                InkWell(
                                  onTap: () => _search(query),
                                  borderRadius:
                                      BorderRadius.circular(14),
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 16, vertical: 14),
                                    child: Row(
                                      children: [
                                        Expanded(
                                          child: Text(query,
                                              style: const TextStyle(
                                                  fontSize: 14,
                                                  color: _textPrimary)),
                                        ),
                                        GestureDetector(
                                          onTap: () =>
                                              _removeRecent(query),
                                          child: const Icon(Icons.close,
                                              size: 16,
                                              color: _textSecondary),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                if (i < _recentSearches.length - 1)
                                  const Divider(
                                      height: 1,
                                      thickness: 1,
                                      color: _divider,
                                      indent: 16,
                                      endIndent: 16),
                              ],
                            );
                          }),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],

                    // ── 인기 검색어 ──
                    const Text('인기 검색어',
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: _textSecondary)),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _popularSearches
                          .map((keyword) => GestureDetector(
                                onTap: () => _search(keyword),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 16, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: _cardBg,
                                    borderRadius:
                                        BorderRadius.circular(20),
                                    border: Border.all(
                                        color:
                                            const Color(0xFFE0E0E0)),
                                  ),
                                  child: Text(keyword,
                                      style: const TextStyle(
                                          fontSize: 13,
                                          color: _textPrimary)),
                                ),
                              ))
                          .toList(),
                    ),
                    const SizedBox(height: 24),

                    // ── 카테고리별 탐색 ──
                    const Text('카테고리별 탐색',
                        style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: _textSecondary)),
                    const SizedBox(height: 10),
                    Container(
                      decoration: BoxDecoration(
                        color: _cardBg,
                        borderRadius: BorderRadius.circular(14),
                        border:
                            Border.all(color: const Color(0xFFE8E8E8)),
                      ),
                      child: Column(
                        children: [
                          _buildCategoryRow(
                            icon: Icons.medication_outlined,
                            label: '내 약물',
                            route: 'medication_list',
                          ),
                          const Divider(
                              height: 1,
                              thickness: 1,
                              color: _divider,
                              indent: 16,
                              endIndent: 16),
                          _buildCategoryRow(
                            icon: Icons.description_outlined,
                            label: '진료 기록',
                            route: 'medical_records',
                          ),
                          const Divider(
                              height: 1,
                              thickness: 1,
                              color: _divider,
                              indent: 16,
                              endIndent: 16),
                          _buildCategoryRow(
                            icon: Icons.bookmark_outline,
                            label: '가이드 모음',
                            route: 'guides',
                          ),
                          const Divider(
                              height: 1,
                              thickness: 1,
                              color: _divider,
                              indent: 16,
                              endIndent: 16),
                          _buildCategoryRow(
                            icon: Icons.bar_chart_outlined,
                            label: '활성도 기록',
                            route: 'activity',
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryRow({
    required IconData icon,
    required String label,
    required String route,
  }) {
    return InkWell(
      onTap: () => _navigateCategory(route),
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          children: [
            Icon(icon, size: 22, color: _textPrimary),
            const SizedBox(width: 14),
            Expanded(
              child: Text(label,
                  style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: _textPrimary)),
            ),
            const Icon(Icons.chevron_right,
                color: _textSecondary, size: 20),
          ],
        ),
      ),
    );
  }
}