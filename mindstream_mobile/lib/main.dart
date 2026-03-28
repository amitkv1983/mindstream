import 'package:flutter/material.dart';

import 'config.dart';
import 'services/api_service.dart';

void main() {
  runApp(const MindstreamMobileApp());
}

class MindstreamMobileApp extends StatelessWidget {
  const MindstreamMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mindstream Mobile',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HealthCheckScreen(),
    );
  }
}

class HealthCheckScreen extends StatefulWidget {
  const HealthCheckScreen({super.key});

  @override
  State<HealthCheckScreen> createState() => _HealthCheckScreenState();
}

class _HealthCheckScreenState extends State<HealthCheckScreen> {
  final ApiService _apiService = ApiService();
  late final TextEditingController _baseUrlController;

  String _responseText = 'Tap "Test Backend" to call /health';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: AppConfig.baseUrl);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    super.dispose();
  }

  Future<void> _testBackend() async {
    FocusScope.of(context).unfocus();

    setState(() {
      AppConfig.baseUrl = _baseUrlController.text.trim();
      _isLoading = true;
      _responseText = 'Calling ${AppConfig.baseUrl}/health ...';
    });

    final result = await _apiService.getHealth();

    if (!mounted) {
      return;
    }

    setState(() {
      _isLoading = false;
      _responseText = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mindstream Backend Test'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Backend URL',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _baseUrlController,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://192.168.1.13:8000',
              ),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _isLoading ? null : _testBackend,
              child: Text(_isLoading ? 'Testing...' : 'Test Backend'),
            ),
            const SizedBox(height: 24),
            const Text(
              'Response',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade400),
                  borderRadius: BorderRadius.circular(12),
                  color: Colors.grey.shade100,
                ),
                child: SingleChildScrollView(
                  child: SelectableText(
                    _responseText,
                    style: const TextStyle(fontSize: 15),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
