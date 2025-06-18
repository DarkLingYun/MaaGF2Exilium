using System;
using System.IO;
using System.Net;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.Json.Serialization;

using MFAWPF.Views;
using MFAWPF.Helper;
using MaaFramework.Binding;
using MaaFramework.Binding.Custom;
using MaaFramework.Binding.Buffers;

namespace RedeemCodeService
{
    public class RedeemCodeException : Exception
    {
        public ErrorType ErrorType { get; }
        public HttpStatusCode? StatusCode { get; }
        public string RawResponse { get; }

        public RedeemCodeException(
            ErrorType errorType,
            string message,
            HttpStatusCode? statusCode = null,
            string rawResponse = null,
            Exception innerException = null)
            : base(message, innerException)
        {
            ErrorType = errorType;
            StatusCode = statusCode;
            RawResponse = rawResponse;
        }
    }

    public enum ErrorType
    {
        NetworkError,
        InvalidResponse,
        ServerError
    }

    public static class RedeemCodeService
    {
        private static readonly HttpClient _httpClient = new HttpClient();
        public const string BaseUrl = "https://gitee.com/guiluan/GF2_RedeemCode/raw/master";
        public const string FileName = "redeemCode.json";

        public static async Task<string[]> GetRedeemCodesAsync()
        {
            var fullUrl = $"{BaseUrl.TrimEnd('/')}/{FileName}";

            try
            {
                var response = await _httpClient.GetAsync(fullUrl);
                var content = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    throw new RedeemCodeException(
                        ErrorType.ServerError,
                        $"服务器返回错误: {(int)response.StatusCode} - {response.ReasonPhrase}",
                        response.StatusCode,
                        content);
                }

                try
                {
                    var data = JsonSerializer.Deserialize<RedeemCodeResponse>(content);
                    return data?.RedeemCodes ?? throw new RedeemCodeException(
                        ErrorType.InvalidResponse,
                        "响应数据格式无效: redeemCodes字段缺失");
                }
                catch (JsonException ex)
                {
                    throw new RedeemCodeException(
                        ErrorType.InvalidResponse,
                        $"JSON解析失败: {ex.Message}",
                        rawResponse: content,
                        innerException: ex);
                }
            }
            catch (HttpRequestException ex)
            {
                throw new RedeemCodeException(
                    ErrorType.NetworkError,
                    $"网络请求失败: {ex.Message}",
                    ex.StatusCode,
                    innerException: ex);
            }
        }

        private class RedeemCodeResponse
        {
            [property: JsonPropertyName("redeemCodes")]
            public string[] RedeemCodes { get; set; }
        }
    }
}

namespace JsonHelper
{
    public class RedeemCodesData
    {
        [JsonPropertyName("redeemCodes")]
        public List<string> RedeemCodes { get; set; } = new List<string>();
    }

    public class JsonFileHandler
    {
        public static RedeemCodesData LoadOrCreateRedeemCodesFile(string filePath)
        {
            EnsureDirectoryExists(filePath);

            RedeemCodesData data;

            if (File.Exists(filePath))
            {
                try
                {
                    string json = File.ReadAllText(filePath);
                    data = JsonSerializer.Deserialize<RedeemCodesData>(json);

                    // 确保反序列化后的对象有效
                    data.RedeemCodes ??= new List<string>();
                }
                catch (JsonException)
                {
                    // 如果文件内容损坏，创建新文件
                    data = CreateNewFile(filePath);
                }
            }
            else
            {
                data = CreateNewFile(filePath);
            }

            return data;
        }

        private static void EnsureDirectoryExists(string filePath)
        {
            var directory = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }
        }

        private static RedeemCodesData CreateNewFile(string filePath)
        {
            var newData = new RedeemCodesData();
            SaveToFile(filePath, newData);
            return newData;
        }

        public static void SaveToFile(string filePath, RedeemCodesData data)
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };

            string json = JsonSerializer.Serialize(data, options);
            File.WriteAllText(filePath, json);
        }
    }
}

namespace MFAWPF.Custom
{
    using MFAWPF.Extensions;
    // 执行完毕后，回到主页面
    public class BatchRedeemCodeAction : IMaaCustomAction
    {
        public string Name { get; set; } = nameof(BatchRedeemCodeAction);

        public bool Run(in IMaaContext context, in RunArgs args, in RunResults res)
        {

            var localContext = context;

            // 从主界面进入个人界面(需处于主界面)
            Func<bool> enterPersonView = () =>
            {
                Task.Delay(1000).Wait();
                IMaaImageBuffer image = new MaaImageBuffer();
                localContext.GetImage(ref image);
                RecognitionDetail detail;

                if (localContext.TemplateMatch("公用按钮组件/个人信息.png", image, out detail, 0.7, 0, 0, 0, 0))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                return false;
            };

            // 从个人界面返回主界面(需处于个人主页)
            Func<bool> backMainView = () =>
            {
                Task.Delay(1000).Wait();
                IMaaImageBuffer image = new MaaImageBuffer();
                localContext.GetImage(ref image);
                RecognitionDetail detail;

                if (localContext.TemplateMatch("公用按钮组件/主页按钮_black.png", image, out detail, 0.7, 6, 6, 194, 72))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                if (localContext.TemplateMatch("公用按钮组件/主页按钮_gray.png", image, out detail, 0.7, 6, 6, 194, 72))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                return false;
            };

            // 打开兑换申请表(需处于个人主页)
            Func<bool> openRedeemForm = () =>
            {
                Task.Delay(1000).Wait();
                IMaaImageBuffer image = new MaaImageBuffer();
                localContext.GetImage(ref image);
                RecognitionDetail detail;
                if (localContext.OCR("兑换码", image, out detail, 961, 625, 284, 71))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                return false;
            };

            // 关闭兑换申请表(需处于申请表打开页面)
            Func<bool> closeRedeemForm = () =>
            {
                Task.Delay(1000).Wait();
                IMaaImageBuffer image = new MaaImageBuffer();
                localContext.GetImage(ref image);
                RecognitionDetail detail;
                if (localContext.TemplateMatch("公用按钮组件/关闭按钮_black.png", image, out detail, 0.7, 255, 89, 771, 504))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                if (localContext.TemplateMatch("公用按钮组件/关闭按钮_gray.png", image, out detail, 0.7, 255, 89, 771, 504))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y);
                    return true;
                }
                return false;
            };

            // 单次兑换(需处于兑换表打开页面)
            bool SingleExchange(string redeemCode)
            {
                IMaaImageBuffer image = new MaaImageBuffer();
                localContext.GetImage(ref image);
                RecognitionDetail detail;
                if (localContext.OCR("请输入兑换码", image, out detail, 255, 89, 771, 504))
                {
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y); // 进入编辑状态
                    Task.Delay(1200).Wait();
                    localContext.InputText(redeemCode);
                    Task.Delay(1200).Wait();
                    localContext.Click(detail.HitBox.X, detail.HitBox.Y); // 退出编辑状态
                    Task.Delay(1200).Wait();
                    if (localContext.OCR("申请", image, out detail, 471, 493, 335, 86))
                    {
                        localContext.Click(detail.HitBox.X, detail.HitBox.Y); // 提交申请
                        return true;
                    }
                    return false;
                }
                return false;
            }

            // 批量兑换(需处于个人主页)
            bool BatchExchange(string[] redeemCodes)
            {
                var configPath = Path.Combine(AppContext.BaseDirectory, "config");
                var filePath = Path.Combine(configPath, "redeemCode.json");
                var data = JsonHelper.JsonFileHandler.LoadOrCreateRedeemCodesFile(filePath);

                // 使用不区分大小写的比较器，并去除空格
                var comparer = StringComparer.InvariantCultureIgnoreCase;
                List<string> availableCodes = redeemCodes
                    .Select(code => code.Trim())
                    .Except(data.RedeemCodes.Select(c => c.Trim()), comparer)
                    .ToList();

                LoggerService.LogInfo($"有 {availableCodes.Count} 个未测试过的兑换码");

                foreach (string redeemCode in availableCodes)
                {
                    openRedeemForm.Until();
                    // 利用闭包特性传递参数
                    Func<bool> singleExchange = () => SingleExchange(redeemCode);
                    if (singleExchange.Until())
                    {
                        data.RedeemCodes.Add(redeemCode);
                        // 每次成功输入后保存结果，防止重复使用兑换码
                        JsonHelper.JsonFileHandler.SaveToFile(filePath, data);
                    }
                    closeRedeemForm.Until();
                }
                return true;
            }

            try
            {
                var redeemCodes = RedeemCodeService.RedeemCodeService.GetRedeemCodesAsync().GetAwaiter().GetResult();
                LoggerService.LogInfo($"成功拉取 {redeemCodes.Length} 个兑换码");

                if (redeemCodes.Length == 0)
                {
                    LoggerService.LogInfo("无可用兑换码，任务退出");
                    return false;
                }

                enterPersonView.Until();
                BatchExchange(redeemCodes);
                LoggerService.LogInfo("兑换码已经全部自动兑换，任务退出，回到主页面");
                backMainView.Until();
                return true;
            }
            catch (RedeemCodeService.RedeemCodeException ex)
            {
                LoggerService.LogError($"[{ex.ErrorType}] 错误信息: {ex.Message}");

                if (!string.IsNullOrEmpty(ex.RawResponse))
                {
                    LoggerService.LogError($"原始响应: {ex.RawResponse}");
                }

                return false;
            }
            catch (Exception ex)
            {
                LoggerService.LogError(ex.Message);
                return false;
            }
        }

        public void Abort() { }
    }
}