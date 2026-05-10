const String apiBaseUrl = 'http://localhost:8000/api/v1';
const String supabaseUrl = 'https://sxtejwnrovajgbrzdqkl.supabase.co';
const String supabaseAnonKey = 'sb_publishable_Ryso1huoJO2QHPBpS_LDyw_adeix7Yh';

// API Endpoints
const String loginEndpoint = '/auth/login';
const String registerEndpoint = '/auth/register';
const String waterBodiesEndpoint = '/water-bodies';
const String monitoringEndpoint = '/monitoring';
const String alertsEndpoint = '/alerts';
const String encroachmentsEndpoint = '/encroachments';

// Other Constants
const Duration apiTimeout = Duration(seconds: 30);
const int imagesCacheSize = 100 * 1024 * 1024; // 100 MB
