using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace hakoniwa.ar.bridge
{
    public interface IHakoniwaArBridgePlayer
    {
        Task<bool> StartService();
        bool StopService();
    }
    public interface IHakoniwaArBridge
    {
        bool Register(IHakoniwaArBridgePlayer player);
        bool Start();
        bool Stop();
    }
}
