/*-- Mesh Viewer --*/

protected func Initialize()
{
	SetSkyAdjust(RGBa(0,0,0255),RGB(128,128,128));
}


protected func InitializePlayer(int plr, int tx, int ty, object pBase, int iTeam)
{
	SetPlayerZoomByViewRange(plr, 100, 0, PLRZOOM_LimitMin);
	SetPlayerZoomByViewRange(plr, 100, 0, PLRZOOM_LimitMax);
	SetPlayerViewLock(plr, true);
//	SetPlayerZoom(player, 1,1, PLRZOOM_LimitMax);
//	SetPlayerZoom(player, 1,1, PLRZOOM_LimitMin);
	return 1;
}
