using System;
using System.Threading;
using System.Threading.Tasks;

namespace hakoniwa.ar.bridge
{
    public class MockPlayer : IHakoniwaArBridgePlayer
    {
        public Task<bool> StartService(string serverUri)
        {
            Console.WriteLine($"MockPlayer service started with server URI: {serverUri}");
            return Task.FromResult(true);
        }

        public bool StopService()
        {
            Console.WriteLine("MockPlayer service stopped.");
            return true;
        }

        public void UpdatePosition(HakoVector3 position, HakoVector3 rotation)
        {
            Console.WriteLine($"Updating position: {position.X}, {position.Y}, {position.Z} | Rotation: {rotation.X}, {rotation.Y}, {rotation.Z}");
        }

        public void ResetPostion()
        {
            Console.WriteLine("Position reset.");
        }

        public void UpdateAvatars()
        {
            Console.WriteLine("Avatars updated.");
        }
    }

    class MainClass
    {
        static private bool isRunning = false;
        static void Main(string[] args)
        {
            var bridge = new HakoniwaArBridge();
            var player = new MockPlayer();

            if (!bridge.Register(player))
            {
                Console.WriteLine("Failed to register player. Exiting.");
                return;
            }

            if (bridge.Start())
            {
                Console.WriteLine("Hakoniwa AR Bridge is running...");
            }
            else
            {
                Console.WriteLine("Failed to start Hakoniwa AR Bridge.");
                return;
            }

            // メインループで定期的にRunメソッドを呼び出し
            isRunning = true;
            while (isRunning)
            {
                bridge.Run();
                Thread.Sleep(1000); // 1秒間スリープしてから再実行
            }

            // サービスの停止
            if (bridge.Stop())
            {
                Console.WriteLine("Hakoniwa AR Bridge service stopped.");
            }
            else
            {
                Console.WriteLine("Failed to stop Hakoniwa AR Bridge.");
            }
        }
    }
}
