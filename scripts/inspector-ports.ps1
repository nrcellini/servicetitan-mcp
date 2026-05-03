# Shared helpers: pick free TCP ports for MCP Inspector (CLIENT_PORT / SERVER_PORT).

function Get-FirstFreeListenerPort {
    param(
        [int] $StartPort,
        [int] $MaxTries = 64
    )
    for ($i = 0; $i -lt $MaxTries; $i++) {
        $port = $StartPort + $i
        $listener = $null
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
            $listener.Start()
            $listener.Stop()
            return $port
        } catch {
            continue
        } finally {
            if ($listener) {
                try { $listener.Stop() } catch { }
            }
        }
    }
    throw "No free TCP port found starting at $StartPort (tried $MaxTries ports)."
}

function Resolve-InspectorPorts {
    param(
        [int] $ClientPreferred = 6274,
        [int] $ServerPreferred = 6277,
        [switch] $NoAuto
    )
    if ($NoAuto) {
        return @{
            ClientPort = $ClientPreferred
            ServerPort = $ServerPreferred
        }
    }
    $client = Get-FirstFreeListenerPort -StartPort $ClientPreferred
    $server = Get-FirstFreeListenerPort -StartPort $ServerPreferred
    if ($server -eq $client) {
        $server = Get-FirstFreeListenerPort -StartPort ($client + 1)
    }
    return @{
        ClientPort = $client
        ServerPort = $server
    }
}
