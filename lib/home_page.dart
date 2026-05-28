import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'services/auth_service.dart';
import 'main.dart';
import 'login_page.dart';
import 'dashboard_page.dart';
import 'medical_records_page.dart';
import 'guides_page.dart';
import 'notifications_page.dart';
import 'my_page.dart';
import 'chat_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentIndex = 2; // 홈이 가운데(index 2)
  bool _isLoggingOut = false;
  late final AuthService _authService;
  late final List<Widget> _pages;
  DateTime? _lastBackPressed;

  @override
  void initState() {
    super.initState();
    _authService = AuthService(tokenStorage: SecureTokenStorage());
    _pages = [
      const MedicalRecordsPage(),  // 기록 (index 0)
      const ChatPage(),             // 챗봇 (index 1)
      const DashboardPage(),        // 홈 (index 2)
      const NotificationsPage(),    // 알림 (index 3)
      MyPage(
        tokenStorage: SecureTokenStorage(),
        onLogout: _handleLogout,
      ),                            // 마이 (index 4)
    ];
  }

  @override
  void dispose() {
    _authService.dispose();
    super.dispose();
  }

  Future<void> _handleLogout() async {
    if (_isLoggingOut) return;
    setState(() => _isLoggingOut = true);
    try {
      await _authService.logout();
    } catch (_) {}
    if (!mounted) return;
    setState(() => _isLoggingOut = false);
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

  Future<bool> _onWillPop() async {
    if (_currentIndex != 2) {
      setState(() => _currentIndex = 2);
      return false;
    }
    final now = DateTime.now();
    if (_lastBackPressed == null ||
        now.difference(_lastBackPressed!) > const Duration(seconds: 2)) {
      _lastBackPressed = now;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('한 번 더 누르면 앱이 종료됩니다.'),
          duration: Duration(seconds: 2),
        ),
      );
      return false;
    }
    SystemNavigator.pop();
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvoked: (_) => _onWillPop(),
      child: Scaffold(
        body: IndexedStack(
          index: _currentIndex,
          children: _pages,
        ),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() => _currentIndex = index),
          type: BottomNavigationBarType.fixed,
          selectedItemColor: const Color(0xFF2ECC71),
          unselectedItemColor: Colors.grey,
          selectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 11,
          ),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.monitor_heart_outlined),
              activeIcon: Icon(Icons.monitor_heart),
              label: '기록',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.chat_bubble_outline),
              activeIcon: Icon(Icons.chat_bubble),
              label: '챗봇',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined),
              activeIcon: Icon(Icons.home),
              label: '홈',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.notifications_outlined),
              activeIcon: Icon(Icons.notifications),
              label: '알림',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: '마이',
            ),
          ],
        ),
      ),
    );
  }
}