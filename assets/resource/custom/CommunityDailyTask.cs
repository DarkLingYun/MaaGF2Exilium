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

using MFAWPF.Helper;
using MFAWPF.Views;
using MaaFramework.Binding;
using MaaFramework.Binding.Custom;

namespace MFAWPF.Custom;

public class LoginPayload
{
    [JsonPropertyName("account_name")]
    public string AccountName { get; set; }
    [JsonPropertyName("passwd")]
    public string Password { get; set; }
    [JsonPropertyName("source")]
    public string Source { get; set; }
}

public class LoginResponse
{
    [JsonPropertyName("Code")]
    public int Code { get; set; }
    [JsonPropertyName("data")]
    public LoginResponseData Data { get; set; }
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

public static class DailyTasks
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
            var url = "https://gf2-bbs-api.sunborngame.com/login/account";
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

            // First attempt
            var jsonPayload = JsonSerializer.Serialize(payload);
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(url, content);
            var responseBody = await response.Content.ReadAsStringAsync();

            var data = JsonSerializer.Deserialize<LoginResponse>(responseBody, options);

            if (data.Code == 0)
            {
                return data.Data.Account.Token;
            }

            // Second attempt with mail source
            payload.Source = "mail";
            jsonPayload = JsonSerializer.Serialize(payload);
            content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            response = await httpClient.PostAsync(url, content);
            responseBody = await response.Content.ReadAsStringAsync();
            data = JsonSerializer.Deserialize<LoginResponse>(responseBody, options);

            return data.Data.Account.Token;
        }
        catch (Exception ex)
        {
            return ex.Message;
        }
    }

    public static async Task ExchangeItemAsync(int exchangeId, string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.sunborngame.com/community/item/exchange";
            var requestBody = new ExchangeRequestBody { ExchangeId = exchangeId };

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
            LoggerService.LogInfo($"物品兑换: {responseBody}");
        }
        catch (Exception ex)
        {
            LoggerService.LogError($"社区每日操作: 兑换失败, {ex.Message}");
        }
    }

    public static async Task SignInAsync(string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.sunborngame.com/community/task/sign_in";

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
            LoggerService.LogError($"社区每日操作: 登录失败, {ex.Message}");
            throw;
        }
    }

    public static async Task<List<int>> GetTopicListAsync()
    {
        try
        {
            using var httpClient = new HttpClient();
            var url = "https://gf2-bbs-api.sunborngame.com/community/topic/list?sort_type=2";
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
            var data = JsonSerializer.Deserialize<CommunityResponse>(responseBody, options);

            var topicIds = data.Data.List.Take(3).Select(t => t.TopicId).ToList();
            LoggerService.LogInfo($"TopicIDs: {string.Join(", ", topicIds)}");
            return topicIds;
        }
        catch (Exception ex)
        {
            LoggerService.LogInfo($"社区每日操作: Topic获取失败, {ex.Message}");
            return new List<int>();
        }
    }

    public static async Task TopicHandleAsync(int topicId, string token)
    {
        try
        {
            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue(token);
            var baseUrl = $"https://gf2-bbs-api.sunborngame.com/community/topic";

            // View
            var viewUrl = $"{baseUrl}/{topicId}?id={topicId}";
            var response = await httpClient.GetAsync(viewUrl);
            response.EnsureSuccessStatusCode();
            LoggerService.LogInfo($"\nTopicView: {await response.Content.ReadAsStringAsync()}");

            // Like
            var likeUrl = $"{baseUrl}/like/{topicId}?id={topicId}";
            response = await httpClient.GetAsync(likeUrl);
            response.EnsureSuccessStatusCode();
            LoggerService.LogInfo($"\nTopicLike: {await response.Content.ReadAsStringAsync()}");

            // Share
            var shareUrl = $"{baseUrl}/share/{topicId}?id={topicId}";
            response = await httpClient.GetAsync(shareUrl);
            response.EnsureSuccessStatusCode();
            LoggerService.LogInfo($"\nTopicShare: {await response.Content.ReadAsStringAsync()}");
        }
        catch (Exception ex)
        {
            LoggerService.LogInfo($"社区每日操作: Topic操作失败, {ex.Message}");
        }
    }

    public static async Task ExecuteDailyTaskAsync(LoginPayload userPayload)
    {
        LoggerService.LogInfo("社区每日操作: 开始");
        try
        {
            var loginTask = LoginAsync(userPayload);
            var topicListTask = GetTopicListAsync();
            await Task.WhenAll(loginTask, topicListTask);

            var jwtToken = loginTask.Result;
            var topicList = topicListTask.Result;

            try
            {
                var tasks = new List<Task> { SignInAsync(jwtToken) };
                tasks.AddRange(topicList.Select(topicId => TopicHandleAsync(topicId, jwtToken)));
                await Task.WhenAll(tasks);
            }
            catch (Exception ex)
            {
                throw;
            }

            try
            {
                var exchangeIds = new[] { 1, 1, 2, 3, 4, 5 };
                foreach (var id in exchangeIds)
                {
                    await ExchangeItemAsync(id, jwtToken);
                    await DelayAsync(1000);
                }
                LoggerService.LogInfo("社区每日操作: 兑换成功");
            }
            catch (Exception ex)
            {
                LoggerService.LogError($"社区每日操作: 兑换失败, {ex.Message}");
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
            throw new ArgumentException("社区每日操作: 密码不能为空");
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

    public bool Run(in IMaaContext context, in RunArgs args)
    {
        try
        {
            var basePath = Path.GetDirectoryName(AppContext.BaseDirectory)
                ?? throw new DirectoryNotFoundException("Unable to find the base directory of the application.");

            // 文件初始化
            string secretDir = Path.Combine(basePath, "config");
            string secretFilePath = Path.Combine(secretDir, "secret.json");

            if (!File.Exists(secretFilePath))
            {
                Directory.CreateDirectory(secretDir);
                var initialContent = new
                {
                    account_name = "source='phone',这里填手机号;source='mail',这里填邮箱",
                    passwd = "",
                    source = "phone"
                };
                string json = JsonSerializer.Serialize(initialContent, new JsonSerializerOptions { WriteIndented = true });
                json = System.Text.RegularExpressions.Regex.Unescape(json);
                File.WriteAllText(secretFilePath, json);
            }

            var options = new JsonSerializerOptions { ReadCommentHandling = JsonCommentHandling.Skip };
            string jsonContent = File.ReadAllText(secretFilePath);
            LoginPayload payload = JsonSerializer.Deserialize<LoginPayload>(jsonContent, options)
                ?? throw new InvalidDataException("反序列化结果为 null");

            LoggerService.LogInfo(payload.Password);
            payload.Password = PasswordHelper.GetMD5HashedPassword(payload.Password);
            DailyTasks.ExecuteDailyTaskAsync(payload).GetAwaiter().GetResult();

            LoggerService.LogInfo("社区每日操作: 执行成功");
            return true;
        }
        catch (Exception ex)
        {
            LoggerService.LogError($"社区每日操作: 执行失败, {ex}");
            GrowlHelper.ErrorGlobal($"社区每日操作: 执行失败, 请检查 `config/secret.json` 文件是否存在。\n初次报错时，默认会在 `config` 目录下创建模板 `secret.json` 文件。如果未创建，也可以手动创建。\n`secret.json`需要填入三个字段：`account_name`, `passwd`, `source`。`account_name`对应账号名；`passwd`对应密码；`source`取值为'phone'或'mail'，对应所用账号是手机号还是邮箱。");
            return false;
        }
    }

    public void Abort() { }
}