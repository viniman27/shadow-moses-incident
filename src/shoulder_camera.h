/* Original Shadow Moses Incident prototype. Included only by DEV_EXE camera.c.
 * Touch the final render view, never GM_Camera's event/callback state.
 * This experiment is intentionally restricted to Loading Dock (s00a).
 */
#ifndef SMI_SHOULDER_CAMERA_H
#define SMI_SHOULDER_CAMERA_H

int SMI_CameraEnabled = 1;
int SMI_CameraActive = 0;
int SMI_CameraCollision = 0;

static void SMI_ApplyShoulderCamera(void)
{
    SVECTOR pivot, eye, target, forward, side, hit;
    int height;
    int saved_map;
    int blocked;
    CONTROL *control;

    SMI_CameraActive = 0;
    SMI_CameraCollision = 0;
    control = GM_PlayerControl;
    if (!control || !control->map || !control->map->hzd ||
        strcmp(GM_GetArea(0), "s00a") != 0)
    {
        return;
    }
    if (GV_PadData[0].press & PAD_L3)
    {
        SMI_CameraEnabled = !SMI_CameraEnabled;
    }
    if (!SMI_CameraEnabled || (GM_GameStatus &
        (STATE_BEHIND_CAMERA | STATE_CUT_IN | STATE_TAKING_PHOTO |
         STATE_DEMO_VERBOSE | STATE_GAME_OVER)) ||
        GM_Camera.first_person || GM_Camera.flag || GM_event_camera_flag)
    {
        return;
    }
    if (GM_PlayerStatus & (PLAYER_PAD_OFF | PLAYER_ACT_ONLY | PLAYER_DAMAGED |
                           PLAYER_DOWNED | PLAYER_GAME_OVER | PLAYER_NOT_PLAYABLE |
                           PLAYER_CAUTION | PLAYER_CB_BOX))
    {
        return;
    }

    height = 1400;
    if (GM_PlayerStatus & PLAYER_GROUND)
    {
        height = 350;
    }
    else if (GM_PlayerStatus & PLAYER_SQUAT)
    {
        height = 850;
    }
    pivot = GM_PlayerPosition;
    /* control.mov is height above the feet, not the ground origin.
     * Match the object's floor-relative basis before adding camera height. */
    pivot.vy += height - control->height;
    /* Flags change before the visible posture animation finishes. Constrain
     * the requested height to the actual head, before querying hazards, so
     * standing up cannot leave the still-prone model below the frame.
     * This local 250-unit envelope preserves the settled dock poses. */
    if (!GM_PlayerBody || !GM_PlayerBody->objs ||
        GM_PlayerBody->objs->n_models <= 6)
    {
        return;
    }
    height = GM_PlayerBody->objs->objs[6].world.t[1];
    if (pivot.vy < height - 250)
    {
        pivot.vy = height - 250;
    }
    else if (pivot.vy > height + 250)
    {
        pivot.vy = height + 250;
    }
    GV_DirVec2(control->rot.vy, 1600, &forward);
    GV_DirVec2(control->rot.vy + 1024, 450, &side);
    eye = pivot;
    eye.vx += side.vx - forward.vx;
    eye.vz += side.vz - forward.vz;
    target = pivot;
    target.vx += forward.vx;
    target.vz += forward.vz;

    /* Query MGS hazards synchronously, then restore the map context. */
    saved_map = GM_CurrentMap;
    GM_SetCurrentMap(control->map->index);
    blocked = HZD_OnlineHazardCheck(control->map->hzd, &pivot, &eye, HZD_CHK_ALL, 0);
    if (blocked)
    {
        HZD_GetOnlinePoint(&hit);
        /* Keep a fixed world-space gap, not 25% of all available room.
         * Proportional padding unnecessarily magnifies Snake near walls.
         * This is still a point-ray constraint, not a near-plane sweep. */
        {
            SVECTOR delta;
            int distance, retained;

            delta.vx = hit.vx - pivot.vx;
            delta.vy = hit.vy - pivot.vy;
            delta.vz = hit.vz - pivot.vz;
            distance = GV_VecLen3(&delta);
            retained = distance > 100 ? distance - 100 : 0;
            eye = pivot;
            if (distance > 0)
            {
                eye.vx += delta.vx * retained / distance;
                eye.vy += delta.vy * retained / distance;
                eye.vz += delta.vz * retained / distance;
            }
        }
        SMI_CameraCollision = 1;
    }
    GM_SetCurrentMap(saved_map);
    gUnkCameraStruct2_800B7868.position = eye;
    gUnkCameraStruct2_800B7868.target = target;
    gUnkCameraStruct2_800B7868.zoom = 320;
    if (blocked)
    {
        SVECTOR boom;
        int zoom;

        /* A wall can leave no room to move the eye farther back. Widen the
         * projection instead of forcing a minimum distance through it.
         * Use the constrained boom, not the animated head, so crawling's
         * head bob does not drive the field of view. These bounds are
         * experimental dock values, not near-plane volume collision. */
        boom.vx = eye.vx - pivot.vx;
        boom.vy = eye.vy - pivot.vy;
        boom.vz = eye.vz - pivot.vz;
        zoom = GV_VecLen3(&boom) * 320 / 1000;
        if (zoom < 192)
        {
            zoom = 192;
        }
        else if (zoom > 320)
        {
            zoom = 320;
        }
        gUnkCameraStruct2_800B7868.zoom = zoom;
    }
    MakeRotate(&eye, &target, &gUnkCameraStruct2_800B7868.rotate,
               &gUnkCameraStruct2_800B7868.track);
    SMI_CameraActive = 1;
}
#endif
