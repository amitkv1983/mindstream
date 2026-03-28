import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';

class ApiService {
  Future<String> getHealth() async {
    final rawBaseUrl = AppConfig.baseUrl.trim();
    if (rawBaseUrl.isEmpty) {
      return 'Error: backend URL is empty.';
    }

    final uri = Uri.parse('$rawBaseUrl/health');

    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        return 'Error: server returned ${response.statusCode}\n${response.body}';
      }

      final dynamic decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) {
        return jsonEncode(decoded);
      }

      return response.body;
    } on TimeoutException {
      return 'Error: request timed out. Check backend URL and network connectivity.';
    } on FormatException {
      return 'Error: invalid backend URL format.';
    } on http.ClientException catch (error) {
      return 'Error: connection failed: $error';
    } catch (error) {
      return 'Error: unexpected failure: $error';
    }
  }
}
