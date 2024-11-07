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
        public HeartBeatRequest(string ipAddress) : base("data", "heartbeat_request")
        {
            Data["ip_address"] = ipAddress;
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
        public PositioningRequest(string frameType, Dictionary<string, float> position, Dictionary<string, float> orientation)
            : base("data", "position")
        {
            Data["frame_type"] = frameType;
            Data["position"] = position;
            Data["orientation"] = orientation;
        }
    }
}
