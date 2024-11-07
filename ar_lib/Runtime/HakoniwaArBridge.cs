using System;
using System.Collections.Generic;

namespace hakoniwa.ar.bridge
{
    public class HakoniwaArBridge: IHakoniwaArBridge
    {
       private IHakoniwaArBridgePlayer player;
        public HakoniwaArBridge()
        {

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
                return false; // すでにプレイヤーが登録されている場合は false を返す
            }

            this.player = player;
            Console.WriteLine("Player registered successfully.");
            return true;
        }

        public bool Start()
        {
            if (player == null)
            {
                Console.WriteLine("No player registered. Cannot start service.");
                return false;
            }

            Console.WriteLine("Hakoniwa AR Bridge service starting...");
            return player.StartService().Result;
        }

        public bool Stop()
        {
            if (player == null)
            {
                Console.WriteLine("No player registered. Nothing to stop.");
                return false;
            }

            Console.WriteLine("Hakoniwa AR Bridge service stopping...");
            return player.StopService();
        }        
    }
}
