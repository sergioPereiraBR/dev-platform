function Show-Tree {
    param(
        [string]$Path = ".",
        [int]$Depth = [int]::MaxValue,
        [switch]$File
    )
    
    Get-ChildItem -Path $Path -Recurse:($Depth -gt 1) -Depth:$Depth |
    Where-Object { $File -or $_.PSIsContainer } |
    Sort-Object FullName |
    ForEach-Object {
        $indent = $_.FullName.Substring($Path.Length).Split('\').Length - 1
        $displayName = $_.Name
        (' ' * 4 * $indent) + "|-- $displayName"
    }
}