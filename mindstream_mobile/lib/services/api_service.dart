import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';

class ChannelCreateResult {
  const ChannelCreateResult({
    required this.isSuccess,
    required this.message,
    this.channelId,
    this.channelName,
  });

  final bool isSuccess;
  final String message;
  final String? channelId;
  final String? channelName;
}

class VideoItem {
  const VideoItem({
    required this.videoId,
    required this.videoUrl,
    this.title,
    this.publishedAt,
    this.channel,
  });

  final String videoId;
  final String videoUrl;
  final String? title;
  final String? publishedAt;
  final String? channel;
}

class VideoFetchResult {
  const VideoFetchResult({
    required this.isSuccess,
    required this.message,
    this.videos = const [],
  });

  final bool isSuccess;
  final String message;
  final List<VideoItem> videos;
}

class ApiService {
  Future<String> getHealth() async {
    final rawBaseUrl = AppConfig.baseUrl.trim();
    if (rawBaseUrl.isEmpty) {
      return 'Backend URL is empty. Please enter a valid backend address.';
    }

    final uri = Uri.parse('$rawBaseUrl/health');

    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        return 'Backend returned an unexpected response. Please try again.';
      }

      final dynamic decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic> && decoded['status'] == 'ok') {
        return 'Backend Status: OK ✅';
      }

      return 'Backend responded, but the response format was unexpected.';
    } on TimeoutException {
      return 'Request timed out. Backend may not be reachable.';
    } on FormatException {
      return 'Backend URL is invalid. Please check the address and try again.';
    } on http.ClientException {
      return 'Cannot connect to backend. Check WiFi and IP.';
    } catch (_) {
      return 'Something went wrong.';
    }
  }

  Future<ChannelCreateResult> createChannel(String urlOrName) async {
    final rawBaseUrl = AppConfig.baseUrl.trim();
    final input = urlOrName.trim();

    if (rawBaseUrl.isEmpty) {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Backend URL is empty. Please enter a valid backend address.',
      );
    }

    if (input.isEmpty) {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Please enter a channel URL or name.',
      );
    }

    final uri = Uri.parse('$rawBaseUrl/channels');

    try {
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'url_or_name': input}),
          )
          .timeout(const Duration(seconds: 15));

      final dynamic decoded = jsonDecode(response.body);

      if (response.statusCode == 200 && decoded is Map<String, dynamic>) {
        final channelId = decoded['id']?.toString();
        final channelName = decoded['name']?.toString();
        if (channelId == null || channelId.isEmpty) {
          return const ChannelCreateResult(
            isSuccess: false,
            message: 'Channel was created, but the response was incomplete.',
          );
        }

        return ChannelCreateResult(
          isSuccess: true,
          message: channelName == null || channelName.isEmpty
              ? 'Channel added successfully.'
              : 'Channel added: $channelName',
          channelId: channelId,
          channelName: channelName,
        );
      }

      if (response.statusCode == 400) {
        return const ChannelCreateResult(
          isSuccess: false,
          message: 'Invalid channel. Please check the channel URL or name.',
        );
      }

      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Backend returned an unexpected response. Please try again.',
      );
    } on TimeoutException {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Request timed out. Backend may not be reachable.',
      );
    } on FormatException {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Backend URL is invalid. Please check the address and try again.',
      );
    } on http.ClientException {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Cannot connect to backend. Check WiFi and IP.',
      );
    } catch (_) {
      return const ChannelCreateResult(
        isSuccess: false,
        message: 'Something went wrong.',
      );
    }
  }

  Future<VideoFetchResult> fetchVideos(String channelId) async {
    final rawBaseUrl = AppConfig.baseUrl.trim();
    final cleanedChannelId = channelId.trim();

    if (rawBaseUrl.isEmpty) {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'Backend URL is empty. Please enter a valid backend address.',
      );
    }

    if (cleanedChannelId.isEmpty) {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'No active channel found. Add a channel first.',
      );
    }

    final uri = Uri.parse('$rawBaseUrl/channels/$cleanedChannelId/videos');

    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 20));
      final dynamic decoded = jsonDecode(response.body);

      if (response.statusCode == 200 && decoded is Map<String, dynamic>) {
        final dynamic videoList = decoded['videos'];
        if (videoList is! List) {
          return const VideoFetchResult(
            isSuccess: false,
            message: 'Video response format was unexpected.',
          );
        }

        final videos = videoList
            .whereType<Map<String, dynamic>>()
            .map(
              (item) => VideoItem(
                videoId: item['video_id']?.toString() ?? '',
                videoUrl: item['video_url']?.toString() ?? '',
                title: item['title']?.toString(),
                publishedAt: item['published_at']?.toString(),
                channel: item['channel']?.toString(),
              ),
            )
            .where((item) => item.videoId.isNotEmpty)
            .toList();

        if (videos.isEmpty) {
          return const VideoFetchResult(
            isSuccess: true,
            message: 'No videos found.',
            videos: [],
          );
        }

        return VideoFetchResult(
          isSuccess: true,
          message: 'Fetched ${videos.length} video(s).',
          videos: videos,
        );
      }

      if (response.statusCode == 404) {
        return const VideoFetchResult(
          isSuccess: false,
          message: 'Channel not found. Please add the channel again.',
        );
      }

      if (response.statusCode == 400) {
        return const VideoFetchResult(
          isSuccess: false,
          message: 'Could not fetch videos for this channel.',
        );
      }

      return const VideoFetchResult(
        isSuccess: false,
        message: 'Backend returned an unexpected response. Please try again.',
      );
    } on TimeoutException {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'Request timed out. Backend may not be reachable.',
      );
    } on FormatException {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'Backend URL is invalid. Please check the address and try again.',
      );
    } on http.ClientException {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'Cannot connect to backend. Check WiFi and IP.',
      );
    } catch (_) {
      return const VideoFetchResult(
        isSuccess: false,
        message: 'Something went wrong.',
      );
    }
  }
}
