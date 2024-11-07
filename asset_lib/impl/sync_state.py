from enum import Enum, auto

class SyncState(Enum):
    WAITING = auto()           # 待機モード
    POSITIONING = auto()       # 位置合わせモード
    PLAYING = auto()           # プレイモード

class SyncStateManagement:
    def __init__(self):
        self.state = SyncState.WAITING

    def connect_established(self):
        """接続確立：待機モードから位置合わせモードへ遷移"""
        if self.state == SyncState.WAITING:
            print("Transitioning from WAITING to POSITIONING")
            self.state = SyncState.POSITIONING

    def start_play(self):
        """プレイ開始：位置合わせモードからプレイモードへ遷移"""
        if self.state == SyncState.POSITIONING:
            print("Transitioning from POSITIONING to PLAYING")
            self.state = SyncState.PLAYING

    def disconnect_or_reset(self):
        """接続切断/リセット：任意の状態から待機モードへ遷移"""
        #print("Transitioning to WAITING (disconnection/reset)")
        self.state = SyncState.WAITING
