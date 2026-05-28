import 'package:flutter/material.dart';
import 'services/user_service.dart';
import 'services/ocr_service.dart';
import 'user_edit_page.dart';
import 'ocr_history_page.dart';
import 'notification_toggle_page.dart';

class MyPage extends StatefulWidget {
  final TokenStorage tokenStorage;
  final VoidCallback? onLogout;

  const MyPage({
    super.key,
    required this.tokenStorage,
    this.onLogout,
  });

  @override
  State<MyPage> createState() => _MyPageState();
}

class _MyPageState extends State<MyPage> {
  late final UserService _userService;

  bool _loading = true;
  String? _error;
  UserProfile? _profile;

  static const _green = Color(0xFF2ECC71);
  static const _greenLight = Color(0xFFE8F8F0);
  static const _bg = Color(0xFFF8FAF8);
  static const _cardBg = Colors.white;
  static const _textPrimary = Color(0xFF1A1A1A);
  static const _textSecondary = Color(0xFF888888);
  static const _divider = Color(0xFFF0F0F0);
  static const _purple = Color(0xFF7C5CCF);
  static const _purpleLight = Color(0xFFF0E8FF);

  @override
  void initState() {
    super.initState();
    _userService = UserService(tokenStorage: widget.tokenStorage);
    _loadProfile();
  }

  @override
  void dispose() {
    _userService.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    setState(() { _loading = true; _error = null; });
    try {
      final profile = await _userService.getMe();
      if (mounted) setState(() => _profile = profile);
    } on AuthException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = '정보를 불러올 수 없습니다.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  bool get _isAutoimmune => _profile?.userType == 'autoimmune';
  Color get _themeColor => _isAutoimmune ? _purple : _green;
  Color get _themeLightColor => _isAutoimmune ? _purpleLight : _greenLight;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: SafeArea(
        child: _loading
            ? Center(child: CircularProgressIndicator(color: _themeColor))
            : _error != null
                ? _buildError()
                : _buildBody(),
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
            onPressed: _loadProfile,
            child: Text('다시 시도', style: TextStyle(color: _themeColor)),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => widget.onLogout?.call(),
            child: const Text('로그아웃',
                style: TextStyle(color: Colors.red, fontSize: 15)),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    return RefreshIndicator(
      onRefresh: _loadProfile,
      color: _themeColor,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('마이페이지',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: _textPrimary)),
            const SizedBox(height: 20),
            _buildProfileCard(),
            const SizedBox(height: 8),
            _buildTypeBadge(),
            const SizedBox(height: 20),
            _sectionLabel('내 건강 정보'),
            const SizedBox(height: 8),
            _buildMenuCard(_healthMenuItems),
            const SizedBox(height: 20),
            _sectionLabel('앱 설정'),
            const SizedBox(height: 8),
            _buildMenuCard(_appSettingsMenuItems),
            const SizedBox(height: 20),
            _sectionLabel('지원'),
            const SizedBox(height: 8),
            _buildMenuCard(_supportMenuItems),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileCard() {
    final profile = _profile;
    final heightStr = profile?.height != null ? '${profile!.height!.toStringAsFixed(0)}cm' : '-';
    final weightStr = profile?.weight != null ? '${profile!.weight!.toStringAsFixed(0)}kg' : '-';
    final birthStr = profile?.birthDate?.replaceAll('-', '.') ?? '-';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 52, height: 52,
                decoration: BoxDecoration(color: _themeLightColor, shape: BoxShape.circle),
                child: Icon(Icons.person_outline, color: _themeColor, size: 28),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(profile?.name ?? '-',
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: _textPrimary)),
                    const SizedBox(height: 2),
                    Text(profile?.email ?? '-',
                        style: const TextStyle(fontSize: 13, color: _textSecondary)),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right, color: _textSecondary, size: 22),
                onPressed: () => _navigate('user_edit'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(child: _buildStatBox('키 / 몸무게', '$heightStr / $weightStr')),
              const SizedBox(width: 10),
              Expanded(child: _buildStatBox('생년월일', birthStr)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatBox(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(color: _bg, borderRadius: BorderRadius.circular(10)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: _textSecondary)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: _textPrimary)),
        ],
      ),
    );
  }

  Widget _buildTypeBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(color: _themeColor, borderRadius: BorderRadius.circular(20)),
      child: Text(
        _isAutoimmune ? '자가면역' : '일반',
        style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700),
      ),
    );
  }

  List<_MenuItem> get _healthMenuItems => _isAutoimmune
      ? [
          _MenuItem(icon: Icons.description_outlined, label: '질환 정보', route: 'disease_info'),
          _MenuItem(icon: Icons.medication_outlined, label: '약물 목록', route: 'medication_list'),
          _MenuItem(icon: Icons.monitor_heart_outlined, label: '위험요인 프로필', route: 'risk_profile'),
          _MenuItem(icon: Icons.folder_outlined, label: '문서 보관함', route: 'documents'),
        ]
      : [
          _MenuItem(icon: Icons.description_outlined, label: '진료 기록', route: 'medical_records'),
          _MenuItem(icon: Icons.medication_outlined, label: '약물 목록', route: 'medication_list'),
          _MenuItem(icon: Icons.monitor_heart_outlined, label: '건강 수치 기록', route: 'health_metrics'),
          _MenuItem(icon: Icons.folder_outlined, label: '문서 보관함', route: 'documents'),
        ];

  List<_MenuItem> get _appSettingsMenuItems => [
        _MenuItem(icon: Icons.notifications_none_outlined, label: '알림 설정', route: 'notification_settings'),
        _MenuItem(icon: Icons.swap_horiz_outlined, label: '모드 전환', route: 'mode_switch'),
        _MenuItem(icon: Icons.settings_outlined, label: '설정', route: 'settings'),
      ];

  List<_MenuItem> get _supportMenuItems => [
        _MenuItem(icon: Icons.help_outline, label: '도움말', route: 'help'),
        _MenuItem(icon: Icons.campaign_outlined, label: '문의하기', route: 'contact'),
        _MenuItem(icon: Icons.logout, label: '로그아웃', route: 'logout', isDestructive: true),
      ];

  Widget _buildMenuCard(List<_MenuItem> items) {
    return Container(
      decoration: BoxDecoration(
        color: _cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE8E8E8)),
      ),
      child: Column(
        children: List.generate(items.length, (i) {
          final item = items[i];
          return Column(
            children: [
              _buildMenuRow(item),
              if (i < items.length - 1)
                const Divider(height: 1, thickness: 1, color: _divider, indent: 16, endIndent: 16),
            ],
          );
        }),
      ),
    );
  }

  Widget _buildMenuRow(_MenuItem item) {
    return InkWell(
      onTap: () => _handleMenuTap(item.route),
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Icon(item.icon, size: 22, color: item.isDestructive ? Colors.red : _textPrimary),
            const SizedBox(width: 14),
            Expanded(
              child: Text(item.label,
                  style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: item.isDestructive ? Colors.red : _textPrimary)),
            ),
            Icon(Icons.chevron_right,
                color: item.isDestructive ? Colors.red.withOpacity(0.5) : _textSecondary,
                size: 20),
          ],
        ),
      ),
    );
  }

  void _handleMenuTap(String route) {
    if (route == 'logout') { _confirmLogout(); return; }
    _navigate(route);
  }

  void _navigate(String route) {
    if (route == 'user_edit' && _profile != null) {
      Navigator.push(context, MaterialPageRoute(
        builder: (_) => UserEditPage(
          tokenStorage: widget.tokenStorage,
          profile: _profile!,
          onWithdraw: widget.onLogout,
        ),
      ));
      return;
    }
    if (route == 'documents') {
      Navigator.push(context, MaterialPageRoute(
        builder: (_) => const OcrHistoryPage(),
      ));
      return;
    }
    if (route == 'notification_settings') {
      Navigator.push(context, MaterialPageRoute(
        builder: (_) => const NotificationTogglePage(),
      ));
      return;
    }
    debugPrint('Navigate to: $route');
  }

  void _confirmLogout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('로그아웃',
            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
        content: const Text('로그아웃 하시겠습니까?', style: TextStyle(fontSize: 15)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소', style: TextStyle(color: _textSecondary)),
          ),
          TextButton(
            onPressed: () { Navigator.pop(ctx); widget.onLogout?.call(); },
            child: const Text('로그아웃',
                style: TextStyle(color: Colors.red, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _sectionLabel(String text) {
    return Text(text,
        style: const TextStyle(fontSize: 13, color: _textSecondary, fontWeight: FontWeight.w500));
  }
}

class _MenuItem {
  final IconData icon;
  final String label;
  final String route;
  final bool isDestructive;

  const _MenuItem({
    required this.icon,
    required this.label,
    required this.route,
    this.isDestructive = false,
  });
}