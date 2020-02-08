
local rotation = 0;
local rotation_speed = 0;

local rotation2 = 0;
local rotation_speed2 = 0;

local zoom = 1000;

local last_x = 0;
local last_y = 0;

local mouse_down = 0;

local target_id = TestObject;

public func Initialize()
{
	SetGraphics(0, target_id);
	SetAction("Float");
	SetPosition(LandscapeWidth()/2, LandscapeHeight()/2);
	AddEffect("Rotation", this, 1, 1, this);
	SetPlayerControlEnabled(0, CON_Aim, true);
}

func SetAnimation(name, speed)
{
	if(speed == nil)
		speed = 40;
	StopAnimation(GetRootAnimation(5));
	PlayAnimation(name, 5, Anim_Linear(0, 0, GetAnimationLength(name), speed, ANIM_Loop), Anim_Const(500));
}

local animation_counter = 0;

func NextAnimation()
{
	animation_counter += 1;
	var anims = target_id->GetAnimationList();
	if(GetLength(anims) <= animation_counter)
	   animation_counter = 0;
	var anim = anims[animation_counter];
	Log(anim);
	SetAnimation(anim);
}

func PrevAnimation()
{
	animation_counter -= 1;
	var anims = target_id->GetAnimationList();
	if(animation_counter < 0)
		animation_counter = GetLength(anims)-1;
	var anim = anims[animation_counter];
	Log(anim);
	SetAnimation(anim);
}

/* Main control function */
public func ObjectControl(int plr, int ctrl, int x, int y, int strength, bool repeat, bool release)
{
	if (!this) 
		return false;
	
	//if( ctrl != CON_Aim)
	//	Log("%d %d %d", x, y, ctrl);
	if(ctrl == CON_Reset)
	{
		zoom = 1000;
		rotation = 0;
		rotation2 = 0;
		return true;
	}
	if(ctrl == CON_Next)
		NextAnimation();
	if(ctrl == CON_Prev)
		PrevAnimation();
	if(ctrl == CON_ScaleUp)
	{
		zoom = zoom*11/10;
		return true;
	}
	if(ctrl == CON_ScaleDown)
	{
		zoom = zoom*9/10;
		return true;
	}
	if(ctrl == CON_Use)
	{
		if(release)
		{
			mouse_down = 0;
		}
		else
		{
			last_x = x;
			last_y = y;
			mouse_down = 1;
		}
	}
	if(ctrl == CON_Aim && mouse_down)
	{
		rotation += (x-last_x)/5;
		rotation2 -= (y-last_y)/5;
		last_x = x;
		last_y = y;
	}
	
	if (ctrl == CON_Left)
	{
		if(release)
		{
			if(rotation_speed == -1)
				rotation_speed = 0;
		}
		else
			rotation_speed = -1;
	}
	if (ctrl == CON_Right)
	{
		if(release)
		{
			if(rotation_speed == +1)
				rotation_speed = 0;
		}
		else
			rotation_speed = +1;
	}
	if (ctrl == CON_Up)
	{
		if(release)
		{
			if(rotation_speed2 == +1)
				rotation_speed2 = 0;
		}
		else
			rotation_speed2 = +1;
	}
	if (ctrl == CON_Down)
	{
		if(release)
		{
			if(rotation_speed2 == -1)
				rotation_speed2 = 0;
		}
		else
			rotation_speed2 = -1;
	}
	
	
}

func FxRotationTimer()
{
	rotation += rotation_speed*5;
	rotation2 += rotation_speed2*5;
	SetProperty("MeshTransformation", Trans_Mul(Trans_Rotate(rotation2,1,0,0), Trans_Rotate(rotation,0,1,0), Trans_Translate(0, 0)));
	SetObjDrawTransform(zoom, 0, 0, 0, zoom, 0, 0);
}

local ActMap = {

Float = {
	Prototype = Action,
	Name = "Float",
	Procedure = DFA_FLOAT,
	Length = 1,
	Delay = 0,
},
};
