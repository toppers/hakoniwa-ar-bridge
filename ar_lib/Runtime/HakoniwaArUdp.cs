using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Newtonsoft.Json;

namespace hakoniwa.ar.bridge
{
    public class UdpComm
    {
        private readonly UdpClient udpClient;
        private IPEndPoint receiveEndPoint;
        private IPEndPoint sendEndPoint;
        private readonly Dictionary<string, BasePacket> packetBuffer;
        private readonly object bufferLock = new object();
        private bool running = false;
        private Thread receiveThread;
        private DateTime lastReceiveTime;

        private readonly int recvPort = 38528;
        private readonly int sendPort = 48528; 

        public UdpComm()
        {
            // ローカルIPを自動的に取得
            string localIp = GetLocalIpAddress();
            receiveEndPoint = new IPEndPoint(IPAddress.Parse(localIp), recvPort);
            udpClient = new UdpClient(recvPort);
            packetBuffer = new Dictionary<string, BasePacket>();
            lastReceiveTime = DateTime.Now;
        }

        public DateTime GetLastReceiveTime()
        {
            return lastReceiveTime;
        }

        public void StartReceiving()
        {
            if (running) return;
            running = true;
            receiveThread = new Thread(ReceiveLoop) { IsBackground = true };
            receiveThread.Start();
            Console.WriteLine("UdpComm receiving started.");
        }

        public void Stop()
        {
            running = false;
            udpClient.Close();
            if (receiveThread != null && receiveThread.IsAlive)
            {
                receiveThread.Join();
            }
            Console.WriteLine("UdpComm stopped.");
        }

        public void SendPacket(BasePacket packet)
        {
            if (sendEndPoint == null)
            {
                Console.WriteLine("No send endpoint available. Please receive a packet first to set the endpoint.");
                return;
            }

            try
            {
                string json = packet.ToJson();
                byte[] data = Encoding.UTF8.GetBytes(json);
                udpClient.Send(data, data.Length, sendEndPoint);
                Console.WriteLine($"Sent packet: {json}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending packet: {ex.Message}");
            }
        }

        private void ReceiveLoop()
        {
            while (running)
            {
                try
                {
                    byte[] data = udpClient.Receive(ref receiveEndPoint);
                    string json = Encoding.UTF8.GetString(data);
                    BasePacket packet = JsonConvert.DeserializeObject<BasePacket>(json);

                    lock (bufferLock)
                    {
                        lastReceiveTime = DateTime.Now;
                        sendEndPoint = new IPEndPoint(receiveEndPoint.Address, sendPort);
                        if (packet.DataType != null)
                        {
                            packetBuffer[packet.DataType] = packet;
                        }
                    }

                    Console.WriteLine($"Received packet from {receiveEndPoint.Address}:{receiveEndPoint.Port}: {json}");
                }
                catch (SocketException ex)
                {
                    if (running)
                    {
                        Console.WriteLine($"Socket error: {ex.Message}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error receiving data: {ex.Message}");
                }
            }
        }

        public BasePacket GetLatestPacket(string packetType)
        {
            lock (bufferLock)
            {
                packetBuffer.TryGetValue(packetType, out var packet);
                return packet;
            }
        }

        private string GetLocalIpAddress()
        {
            using (var socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, 0))
            {
                socket.Connect("8.8.8.8", 65530); // 外部アドレスに接続してローカルIPを取得
                return ((IPEndPoint)socket.LocalEndPoint).Address.ToString();
            }
        }
    }
}
