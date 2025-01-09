using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace hakoniwa.ar.bridge
{
    public class BasePacket
    {
        [JsonProperty("type")]
        public string PacketType { get; set; }  // "data" or "event"

        [JsonProperty("data_type")]
        public string DataType { get; set; }  // Required if type is "data"

        [JsonProperty("event_type")]
        public string EventType { get; set; }  // Required if type is "event"

        [JsonProperty("data")]
        public Dictionary<string, object> Data { get; set; }  // Additional data (only if type is "data")

        public BasePacket(string packetType, string dataType = null, string eventType = null)
        {
            PacketType = packetType;
            DataType = dataType;
            EventType = eventType;
            Data = new Dictionary<string, object>();
        }

        public string ToJson()
        {
            return JsonConvert.SerializeObject(this);
        }

        public static BasePacket FromJson(string json)
        {
            return JsonConvert.DeserializeObject<BasePacket>(json);
        }
    }

    public class HeartBeatRequest : BasePacket
    {
        public HeartBeatRequest(string ipAddress, int server_udp_port, PositioningRequestData pos) : base("data", "heartbeat_request")
        {
            Data["ip_address"] = ipAddress;
            Data["server_udp_port"] = server_udp_port;
            Data["saved_position"] = pos;
        }
        // BasePacketからHeartBeatRequestに変換するためのメソッド
        static public HeartBeatRequest FromBasePacket(BasePacket basePacket)
        {
            if (basePacket.PacketType != "data" || basePacket.DataType != "heartbeat_request")
            {
                throw new ArgumentException("Invalid packet type or data type for HeartBeatRequest.");
            }

            // data を再度 JSON にシリアライズしてから、HeartBeatRequest にデシリアライズ
            var dataJson = JsonConvert.SerializeObject(basePacket.Data);
            var data = JsonConvert.DeserializeObject<HeartBeatRequest>(dataJson);

            if (data == null || data.Data == null || data.Data["ip_address"] == null || data.Data["server_udp_port"] == null || data.Data["saved_position"] == null)
            {
                throw new ArgumentException($"Invalid data format in BasePacket for HeartBeatRequest: {dataJson}");
            }

            return data;
        }
    }

    public class HeartBeatResponse : BasePacket
    {
        public HeartBeatResponse(string status) : base("data", "heartbeat_response")
        {
            Data["status"] = status;
        }
    }

    public class EventRequest : BasePacket
    {
        public EventRequest(string eventType) : base("event", null, eventType)
        {
            if (eventType != "play_start" && eventType != "reset")
            {
                throw new ArgumentException("Invalid event type. Expected 'play_start' or 'reset'.");
            }
        }
    }
    public class PositioningRequest : BasePacket
    {
        public string FrameType { get; set; }
        public Dictionary<string, double> Position { get; set; }
        public Dictionary<string, double> Orientation { get; set; }

        public PositioningRequest(string frameType, Dictionary<string, double> position, Dictionary<string, double> orientation)
            : base("data", "position")
        {
            FrameType = frameType;
            Position = position;
            Orientation = orientation;
        }

        // BasePacketからPositioningRequestに変換するためのメソッド
        public static HeartBeatRequestData FromBasePacket(BasePacket basePacket)
        {
            if (basePacket.PacketType != "data" || basePacket.DataType != "position")
            {
                throw new ArgumentException("Invalid packet type or data type for PositioningRequest.");
            }

            // data を再度 JSON にシリアライズしてから、PositioningRequest にデシリアライズ
            var dataJson = JsonConvert.SerializeObject(basePacket.Data);
            var data = JsonConvert.DeserializeObject<PositioningRequestData>(dataJson);

            if (data == null || data.Position == null || data.Orientation == null)
            {
                throw new ArgumentException($"Invalid data format in BasePacket for PositioningRequest: {dataJson}");
            }

            return data;
        }

    }

    // HeartBeatRequestの内部データ構造
    public class HeartBeatRequestData
    {
        [JsonProperty("ip_address")]
        public string IpAddress { get; set; }

        [JsonProperty("server_udp_port")]
        public int ServerUdpPort { get; set; }

        [JsonProperty("saved_position")]
        public PositioningRequestData SavedPosition { get; set; }
    }

    // PositioningRequestの内部データ構造
    public class PositioningRequestData
    {
        [JsonProperty("frame_type")]
        public string FrameType { get; set; }

        [JsonProperty("position")]
        public Dictionary<string, double> Position { get; set; }

        [JsonProperty("orientation")]
        public Dictionary<string, double> Orientation { get; set; }
    }
}
