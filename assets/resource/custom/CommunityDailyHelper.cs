using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using System.Diagnostics;
using System.IO;
using MaaFramework.Binding;
using MaaFramework.Binding.Custom;
using MFAAvalonia.Helper;

namespace MFAAvalonia.Custom;

public class LoginPayload
{
    [JsonPropertyName("account_name")]
    public string AccountName { get; set; }
    [JsonPropertyName("passwd")]
    public string Password { get; set; }
    [JsonPropertyName("source")]
    public string? Source { get; set; }
}

public class LoginResponse
{
    [JsonPropertyName("Code")]
    public int Code { get; set; }
    [JsonPropertyName("Message")]
    public string Message { get; set; }
    [JsonPropertyName("data")]
    public object Data { get; set; }
}

public class LoginResponseData
{
    [JsonPropertyName("account")]
    public Account Account { get; set; }
}

public class Account
{
    [JsonPropertyName("token")]
    public string Token { get; set; }
}

public class CommunityResponse
{
    [JsonPropertyName("data")]
    public CommunityData Data { get; set; }
}

public class CommunityData
{
    [JsonPropertyName("list")]
    public List<Topic> List { get; set; } = new List<Topic>();
}

public class Topic
{
    [JsonPropertyName("topic_id")]
    public int TopicId { get; set; }
}

public class ExchangeRequestBody
{
    [JsonPropertyName("exchange_id")]
    public int ExchangeId { get; set; }
}

public static class CommunityDailyHelper
{
    public static async Task DelayAsync(int milliseconds)
    {
        await Task.Delay(milliseconds);
    }

    public static async Task<string> LoginAsync(LoginPayload payload)
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.exiliumgf.com/login/account";
            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            // 使用用户配置的 source 值
            var jsonPayload = JsonSerializer.Serialize(payload);
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            var responseBody = await response.Content.ReadAsStringAsync();

            var loginResponse = JsonSerializer.Deserialize<LoginResponse>(responseBody, options);

            if (loginResponse.Code == 0)
            {
                var data = JsonSerializer.Deserialize<LoginResponseData>(JsonSerializer.Serialize(loginResponse.Data));
                return data.Account.Token;
            }

            throw new ArgumentException($"用户名或密码错误. 请检查 `config/secret.json` 是否正确填写. `config/secret.json` 要填入三个字段: account_name 对应账户名称, passwd 对应密码密文, source 对应账户类型(mail或phone).");
        }
        catch (Exception ex)
        {
            throw;
        }
    }

    public static async Task ExchangeItemAsync(int exchangeId, string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.exiliumgf.com/community/item/exchange";
            var requestBody = new ExchangeRequestBody
            {
                ExchangeId = exchangeId
            };

            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var request = new HttpRequestMessage(HttpMethod.Post, url)
            {
                Content = content
            };
            request.Headers.Authorization = new AuthenticationHeaderValue(token);

            var response = await httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
            LoggerHelper.Info($"物品兑换: {responseBody}");
        }
        catch (Exception ex)
        {
            LoggerHelper.Error($"社区每日操作: 兑换失败, {ex.Message}");
        }
    }

    public static async Task SignInAsync(string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.exiliumgf.com/community/task/sign_in";

            var request = new HttpRequestMessage(HttpMethod.Post, url)
            {
                Content = new StringContent("{}", Encoding.UTF8, "application/json")
            };
            request.Headers.Authorization = new AuthenticationHeaderValue(token);

            var response = await httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
        }
        catch (Exception ex)
        {
            LoggerHelper.Error($"社区每日操作: 登录失败, {ex}");
            throw;
        }
    }

    public static async Task<List<int>> GetTopicListAsync()
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.exiliumgf.com/community/topic/list?sort_type=2";
            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
            var data = JsonSerializer.Deserialize<CommunityResponse>(responseBody, options);

            var topicIds = data.Data.List.Take(3).Select(t => t.TopicId).ToList();
            LoggerHelper.Info($"TopicIDs: {string.Join(", ", topicIds)}");
            return topicIds;
        }
        catch (Exception ex)
        {
            LoggerHelper.Info($"社区每日操作: Topic获取失败, {ex.Message}");
            return new List<int>();
        }
    }

    public static async Task TopicHandleAsync(int topicId, string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue(token);
            var baseUrl = $"https://gf2-bbs-api.exiliumgf.com/community/topic";

            // View
            var viewUrl = $"{baseUrl}/{topicId}?id={topicId}";
            var response = await httpClient.GetAsync(viewUrl);
            response.EnsureSuccessStatusCode();
            LoggerHelper.Info($"\nTopicView: {await response.Content.ReadAsStringAsync()}");

            // Like
            var likeUrl = $"{baseUrl}/like/{topicId}?id={topicId}";
            response = await httpClient.GetAsync(likeUrl);
            response.EnsureSuccessStatusCode();
            LoggerHelper.Info($"\nTopicLike: {await response.Content.ReadAsStringAsync()}");

            // Share
            var shareUrl = $"{baseUrl}/share/{topicId}?id={topicId}";
            response = await httpClient.GetAsync(shareUrl);
            response.EnsureSuccessStatusCode();
            LoggerHelper.Info($"\nTopicShare: {await response.Content.ReadAsStringAsync()}");
        }
        catch (Exception ex)
        {
            LoggerHelper.Info($"社区每日操作: Topic操作失败, {ex.Message}");
        }
    }

    public static async Task ExecuteDailyTaskAsync(LoginPayload userPayload)
    {
        LoggerHelper.Info("社区每日操作: 开始");
        try
        {
            var loginTask = LoginAsync(userPayload);
            var topicListTask = GetTopicListAsync();
            await Task.WhenAll(loginTask, topicListTask);

            var jwtToken = loginTask.Result;
            var topicList = topicListTask.Result;

            try
            {
                var tasks = new List<Task>
                {
                    SignInAsync(jwtToken)
                };
                tasks.AddRange(topicList.Select(topicId => TopicHandleAsync(topicId, jwtToken)));
                await Task.WhenAll(tasks);
            }
            catch (Exception ex)
            {
                throw;
            }

            try
            {
                var exchangeIds = new[]
                {
                    1,
                    1,
                    2,
                    3,
                    4,
                    5,
                    7
                };
                foreach (var id in exchangeIds)
                {
                    await ExchangeItemAsync(id, jwtToken);
                    await DelayAsync(1000);
                }
                LoggerHelper.Info("社区每日操作: 兑换成功");
            }
            catch (Exception ex)
            {
                LoggerHelper.Error($"社区每日操作: 兑换失败, {ex}");
            }
        }
        catch (Exception ex)
        {
            throw;
        }
    }
}

public static class PasswordHelper
{
    public static string GetMD5HashedPassword(string password)
    {
        if (string.IsNullOrEmpty(password))
        {
            throw new ArgumentException("密码不能为空, 请检查 `config/secret.json` 内的 passwd 字段是否正确设置");
        }

        using (MD5 md5 = MD5.Create())
        {
            byte[] inputBytes = Encoding.UTF8.GetBytes(password);
            byte[] hashBytes = md5.ComputeHash(inputBytes);

            StringBuilder sb = new StringBuilder();
            foreach (byte b in hashBytes)
            {
                sb.Append(b.ToString("x2"));
            }
            return sb.ToString();
        }
    }
}

public class CommunityDailyAction : IMaaCustomAction
{
    public string Name { get; set; } = nameof(CommunityDailyAction);

    public bool Run<T>(T context, in RunArgs args, in RunResults res) where T : IMaaContext
    {
        try
        {
            var basePath = Path.GetDirectoryName(AppContext.BaseDirectory)
                ?? throw new DirectoryNotFoundException("找不到应用根目录.");

            // 文件初始化
            string secretDir = Path.Combine(basePath, "config");
            string secretFilePath = Path.Combine(secretDir, "secret.json");

            if (!File.Exists(secretFilePath))
            {
                Directory.CreateDirectory(secretDir);
                var initialContent = new
                {
                    account_name = "密文",
                    passwd = "密码密文",
                    source = "phone或mail 根据登录的账号类型填写"
                };
                string json = JsonSerializer.Serialize(initialContent, new JsonSerializerOptions
                {
                    WriteIndented = true
                });
                json = System.Text.RegularExpressions.Regex.Unescape(json);
                File.WriteAllText(secretFilePath, json);
            }

            var options = new JsonSerializerOptions
            {
                ReadCommentHandling = JsonCommentHandling.Skip
            };
            string jsonContent = File.ReadAllText(secretFilePath);
            LoginPayload payload = JsonSerializer.Deserialize<LoginPayload>(jsonContent, options)
                ?? throw new InvalidDataException("反序列化结果为 null");

            // 校验 source 字段
            if (string.IsNullOrEmpty(payload.Source) || 
                (payload.Source != "mail" && payload.Source != "phone"))
            {
                throw new ArgumentException($"source 字段值无效. 请检查 `config/secret.json` 中 source 字段只能为 `mail` 或 `phone`.");
            }

            // 用户已填写密文密码，不再加密
            CommunityDailyHelper.ExecuteDailyTaskAsync(payload).GetAwaiter().GetResult();

            LoggerHelper.Info("社区每日操作: 执行成功");
            return true;
        }
        catch (Exception ex)
        {
            LoggerHelper.Error($"社区每日操作: 执行失败, {ex}");
            ToastHelper.Error($"社区每日操作: 执行失败", ex.Message);
            return false;
        }
    }

    public void Abort() { }
}