import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
  static const _baseUrlPreferenceKey = 'mindstream_base_url';

  final ApiService _apiService = ApiService();
  late final TextEditingController _baseUrlController;
  late final TextEditingController _channelController;

  String _responseText = 'Set the backend URL and tap "Test Backend".';
  String _channelStatusText = 'Add a channel to start the Mindstream flow.';
  String _videoStatusText = 'Fetch videos after adding a channel.';
  String? _activeChannelId;
  List<VideoItem> _videos = const [];
  bool _isLoading = false;
  bool _isAddingChannel = false;
  bool _isFetchingVideos = false;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: AppConfig.baseUrl);
    _channelController = TextEditingController();
    _loadSavedBaseUrl();
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _channelController.dispose();
    super.dispose();
  }

  Future<void> _loadSavedBaseUrl() async {
    final preferences = await SharedPreferences.getInstance();
    final savedBaseUrl = preferences.getString(_baseUrlPreferenceKey);
    if (savedBaseUrl == null || savedBaseUrl.trim().isEmpty) {
      return;
    }

    AppConfig.updateBaseUrl(savedBaseUrl);

    if (!mounted) {
      return;
    }

    setState(() {
      _baseUrlController.text = AppConfig.baseUrl;
    });
  }

  Future<void> _saveBaseUrl(String value) async {
    final cleaned = value.trim();
    AppConfig.updateBaseUrl(cleaned);

    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_baseUrlPreferenceKey, AppConfig.baseUrl);
  }

  Future<void> _testBackend() async {
    FocusScope.of(context).unfocus();
    await _saveBaseUrl(_baseUrlController.text);

    setState(() {
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

  Future<void> _addChannel() async {
    FocusScope.of(context).unfocus();
    await _saveBaseUrl(_baseUrlController.text);

    setState(() {
      _isAddingChannel = true;
      _channelStatusText = 'Adding channel...';
    });

    final result = await _apiService.createChannel(_channelController.text);

    if (!mounted) {
      return;
    }

    setState(() {
      _isAddingChannel = false;
      _channelStatusText = result.message;
      if (result.isSuccess) {
        _activeChannelId = result.channelId;
        _videos = const [];
        _videoStatusText = 'Channel added. Fetch videos to continue.';
      }
    });
  }

  Future<void> _fetchVideos() async {
    FocusScope.of(context).unfocus();
    await _saveBaseUrl(_baseUrlController.text);

    setState(() {
      _isFetchingVideos = true;
      _videoStatusText = 'Fetching videos...';
    });

    final result = await _apiService.fetchVideos(_activeChannelId ?? '');

    if (!mounted) {
      return;
    }

    setState(() {
      _isFetchingVideos = false;
      _videoStatusText = result.message;
      _videos = result.videos;
    });
  }

  String _videoSubtitle(VideoItem video) {
    final parts = <String>[];
    if ((video.channel ?? '').trim().isNotEmpty) {
      parts.add(video.channel!.trim());
    }
    if ((video.publishedAt ?? '').trim().isNotEmpty) {
      parts.add(video.publishedAt!.trim());
    }
    return parts.join(' • ');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mindstream Backend Test'),
      ),
      body: SingleChildScrollView(
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
              onChanged: (value) {
                AppConfig.updateBaseUrl(value);
              },
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://10.0.2.2:8000',
              ),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _isLoading ? null : _testBackend,
              child: Text(_isLoading ? 'Testing...' : 'Test Backend'),
            ),
            if (_isLoading) ...[
              const SizedBox(height: 16),
              const Center(child: CircularProgressIndicator()),
            ],
            const SizedBox(height: 24),
            const Text(
              'Add Channel',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _channelController,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'https://www.youtube.com/@GoogleDevelopers',
              ),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _isAddingChannel ? null : _addChannel,
              child: Text(_isAddingChannel ? 'Adding...' : 'Add Channel'),
            ),
            if (_isAddingChannel) ...[
              const SizedBox(height: 16),
              const Center(child: CircularProgressIndicator()),
            ],
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(12),
                color: Colors.blueGrey.shade50,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _channelStatusText,
                    style: const TextStyle(fontSize: 15),
                  ),
                  if (_activeChannelId != null) ...[
                    const SizedBox(height: 8),
                    SelectableText(
                      'Active channel_id: $_activeChannelId',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Fetch Videos',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: (_isFetchingVideos || _activeChannelId == null)
                  ? null
                  : _fetchVideos,
              child: Text(_isFetchingVideos ? 'Fetching...' : 'Fetch Videos'),
            ),
            if (_isFetchingVideos) ...[
              const SizedBox(height: 16),
              const Center(child: CircularProgressIndicator()),
            ],
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(12),
                color: Colors.orange.shade50,
              ),
              child: Text(
                _videoStatusText,
                style: const TextStyle(fontSize: 15),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              height: 280,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(12),
                color: Colors.white,
              ),
              child: _videos.isEmpty
                  ? const Center(
                      child: Text(
                        'No videos loaded yet.',
                        style: TextStyle(fontSize: 15),
                      ),
                    )
                  : ListView.separated(
                      itemCount: _videos.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final video = _videos[index];
                        final subtitle = _videoSubtitle(video);
                        return ListTile(
                          leading: const Icon(Icons.ondemand_video),
                          title: Text(
                            (video.title ?? '').trim().isEmpty
                                ? video.videoId
                                : video.title!.trim(),
                          ),
                          subtitle: subtitle.isEmpty ? null : Text(subtitle),
                          dense: false,
                        );
                      },
                    ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Response',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 140,
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
