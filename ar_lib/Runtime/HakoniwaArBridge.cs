using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace hakoniwa.ar.bridge
{
    public enum BridgeState
    {
        POSITIONING,
        PLAYING
    }
    public class HakoniwaArBridge: IHakoniwaArBridge
    {
        private readonly int heartbeatTimeoutSeconds = 5;
        private DateTime lastHeartbeatTime = DateTime.Now; // 初期値として現在時刻を設定
        private IHakoniwaArBridgePlayer player;
        private UdpComm udp_service;
        private BridgeState state;
        private string serverUri;

        public HakoniwaArBridge()
        {
            state = BridgeState.POSITIONING;
            udp_service = new UdpComm();
        }

        public bool Register(IHakoniwaArBridgePlayer player)
        {
            if (player == null)
            {
                throw new ArgumentNullException(nameof(player));
            }

            if (this.player != null)
            {
                Console.WriteLine("A player is already registered.");
                return false;
            }

            this.player = player;
            Console.WriteLine("Player registered successfully.");
            return true;
        }

        private void HeartBeatCheck()
        {
            var packet = udp_service.GetLatestPacket("heartbeat_request");

            if (packet != null && packet.Data != null && packet.Data.ContainsKey("ip_address"))
            {
                // ハートビートを受信したため、タイムスタンプを更新
                lastHeartbeatTime = DateTime.Now;

                var ipAddress = packet.Data["ip_address"] as string;
                serverUri = $"ws://{ipAddress}:8065";

                // 現在の状態を文字列として取得し、HeartBeatResponseに設定
                var reply = new HeartBeatResponse(state.ToString());
                udp_service.SendPacket(reply);
                Console.WriteLine($"Heartbeat response sent with state: {state.ToString()} to {serverUri}");
            }
            else
            {
                if (packet != null) {
                    Console.WriteLine("Invalid or missing IP address in heartbeat_request packet.");
                }
            }

            // タイムアウトチェック: 最後のハートビートから5秒以上経過している場合
            if ((DateTime.Now - lastHeartbeatTime).TotalSeconds > heartbeatTimeoutSeconds)
            {
                Console.WriteLine("Heartbeat timeout detected. Switching to POSITIONING state.");
                state = BridgeState.POSITIONING;
            }
        }
        void RunPositioning()
        {
            var event_packet = udp_service.GetLatestPacket("play_start");
            if (event_packet != null) {
                state = BridgeState.PLAYING;
                return;
            }

            var packet = udp_service.GetLatestPacket("position");
            if (packet == null || packet.Data == null) 
            {
                Console.WriteLine("No position data available in the packet.");
                return;
            }

            try
            {
                // `Data`から座標情報を取得
                var positionData = packet.Data["position"] as Dictionary<string, object>;
                var orientationData = packet.Data["orientation"] as Dictionary<string, object>;

                if (positionData != null && orientationData != null)
                {
                    HakoVector3 pos = new HakoVector3(
                        Convert.ToSingle(positionData["x"]),
                        Convert.ToSingle(positionData["y"]),
                        Convert.ToSingle(positionData["z"])
                    );

                    HakoVector3 rot = new HakoVector3(
                        Convert.ToSingle(orientationData["x"]),
                        Convert.ToSingle(orientationData["y"]),
                        Convert.ToSingle(orientationData["z"])
                    );

                    player.UpdatePosition(pos, rot);
                }
                else
                {
                    Console.WriteLine("Position or orientation data is missing in the packet.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error extracting position and orientation data: {ex.Message}");
            }
        }
        private void RunPlaying()
        {
            var event_packet = udp_service.GetLatestPacket("reset");
            if (event_packet != null) {
                player.ResetPostion();
                udp_service.Stop();
                udp_service = new UdpComm();
                udp_service.StartReceiving();
                state = BridgeState.POSITIONING;
                return;
            }
            player.UpdateAvatars();
        }
        public void Run()
        {
            HeartBeatCheck();
            if (state == BridgeState.POSITIONING) {
                RunPositioning();
            }
            else {
                RunPlaying();
            }
        }

        public bool Start()
        {
            if (player == null)
            {
                Console.WriteLine("No player registered. Cannot start service.");
                return false;
            }

            udp_service.StartReceiving();
            Console.WriteLine("Hakoniwa AR Bridge service starting...");

            try
            {
                return player.StartService(serverUri).GetAwaiter().GetResult(); // 非同期タスクのブロッキングを安全に行う
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error starting player service: {ex.Message}");
                return false;
            }

        }

        public bool Stop()
        {
            if (player == null)
            {
                Console.WriteLine("No player registered. Nothing to stop.");
                return false;
            }

            udp_service.Stop();
            Console.WriteLine("Hakoniwa AR Bridge service stopping...");
            return player.StopService();
        }
    }
}
