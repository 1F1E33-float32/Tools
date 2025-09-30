int __stdcall BSXScript::Fetch(int a1, _DWORD *a2)
{
  int v2; // eax
  int *v3; // esi
  unsigned __int8 *v4; // edi
  _DWORD *v5; // eax
  bool v6; // al
  int v7; // ebx
  int v8; // esi
  int v9; // ecx
  __int16 v10; // bx
  int v11; // eax
  double v12; // st7
  int v13; // eax
  _DWORD *v14; // eax
  double *v15; // eax
  int v16; // edx
  int v17; // eax
  int v18; // ecx
  int v19; // ebx
  int v20; // eax
  int v21; // ecx
  int v22; // edx
  int v24; // ebx
  unsigned __int8 v25; // al
  int v26; // edx
  int v27; // eax
  int v28; // [esp-4h] [ebp-48h]
  char X; // [esp+0h] [ebp-44h]
  char X_4; // [esp+4h] [ebp-40h]
  char v31; // [esp+8h] [ebp-3Ch]
  double *v32; // [esp+1Ch] [ebp-28h]
  _WORD v33[2]; // [esp+28h] [ebp-1Ch] BYREF
  int v34; // [esp+2Ch] [ebp-18h]
  int v35; // [esp+30h] [ebp-14h]
  int v36; // [esp+34h] [ebp-10h]
  int ArgList; // [esp+38h] [ebp-Ch]
  int ArgList_4; // [esp+3Ch] [ebp-8h]

  while ( 2 )
  {
    while ( 1 )
    {
      v2 = *(a1 + 8);
      v3 = 0;
      if ( v2 >= 0 && v2 < *(a1 + 0x5C) )
        break;
      if ( (dword_5A2BF4 & 1) == 0 )
      {
        dword_5A2BF4 |= 1u;
        hObject = 0xFFFFFFFF;
        dword_5A296C = 0;
        memset(&unk_5A2988, 0, 0x208u);
        InitializeCriticalSection(&CriticalSection);
        atexit(sub_561FF0);
      }
      sub_49B340(0, L"BSXX", L"スクリプト領域外が参照されました\n", v31);
      BSXScript::ResetAndJumpBoot(a1);
    }
    v4 = (*(a1 + 0x58) + v2);
    v5 = v4 + 1;
    *a2 = v4 + 1;
    switch ( *v4 )
    {
      case 0u:
        BSXScript::ResetAndJumpBoot(a1);
        return 0;
      case 1u:
        ++*(a1 + 8);
        return 1;
      case 2u:
        return 2;
      case 3u:
        *(a1 + 8) = *(*(a1 + 0x60) + 8 * *v5);
        continue;
      case 4u:
        *(a1 + 8) = *v5;
        continue;
      case 5u:
        if ( !**(a1 + 0x20) )
          goto LABEL_11;
        *(a1 + 8) = *v5;
        continue;
      case 6u:
        if ( **(a1 + 0x20) )
LABEL_11:
          *(a1 + 8) += 5;
        else
          *(a1 + 8) = *v5;
        continue;
      case 7u:
      case 8u:
        *(a1 + 0x1B4) = *(*(a1 + 0x60) + 8 * *v5);
        v6 = *v4 == 8;
        *(a1 + 8) += 5;
        *(a1 + 0x1B8) = v6;
        continue;
      case 9u:
        BSXScript::LabelCall(*(a1 + 8) + 5, *v5);
        continue;
      case 0xAu:
        BSXScript::LabelReturn();
        continue;
      case 0xBu:
        ++*(a1 + 8);
        *(a1 + 0xC) = 0;
        continue;
      case 0xCu:
      case 0xDu:
      case 0xEu:
      case 0xFu:
      case 0x10u:
      case 0x11u:
      case 0x13u:
      case 0x14u:
      case 0x15u:
      case 0x16u:
      case 0x17u:
      case 0x18u:
      case 0x19u:
      case 0x3Au:
      case 0x3Bu:
      case 0x3Cu:
        v7 = *(v4 + 2);
        *(a1 + 8) += 0x12;
        switch ( *(v4 + 3) )
        {
          case 0x100:
            v8 = *(v4 + 2);
            break;
          case 0x102:
            v8 = *(*(a1 + 0x38) + 4 * *(v4 + 2));
            break;
          case 0x103:
            v8 = *(*(a1 + 0x40) + 4 * *(v4 + 2));
            break;
          case 0x104:
            v8 = *(*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 2)));
            break;
          case 0x105:
            v8 = *(*(a1 + 0x20) + 4 * *(v4 + 2));
            break;
          case 0x106:
            v8 = floor(**(*(a1 + 0x48) + 4 * *(v4 + 2)));
            break;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
        switch ( *(v4 + 6) )
        {
          case 0x100:
            v9 = *(v4 + 0xE);
            break;
          case 0x102:
            v9 = *(*(a1 + 0x38) + 4 * *(v4 + 0xE));
            break;
          case 0x103:
            v9 = *(*(a1 + 0x40) + 4 * *(v4 + 0xE));
            break;
          case 0x104:
            v9 = *(*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 0xE)));
            break;
          case 0x105:
            v9 = *(*(a1 + 0x20) + 4 * *(v4 + 0xE));
            break;
          case 0x106:
            v9 = floor(**(*(a1 + 0x48) + 4 * *(v4 + 0xE)));
            break;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
        switch ( *v4 )
        {
          case 0xC:
            *(*(a1 + 0x20) + 4 * v7) = v8 > v9;
            break;
          case 0xD:
            *(*(a1 + 0x20) + 4 * v7) = v8 < v9;
            break;
          case 0xE:
            *(*(a1 + 0x20) + 4 * v7) = v8 >= v9;
            break;
          case 0xF:
            *(*(a1 + 0x20) + 4 * v7) = v8 <= v9;
            break;
          case 0x10:
            *(*(a1 + 0x20) + 4 * v7) = v8 != v9;
            break;
          case 0x11:
            *(*(a1 + 0x20) + 4 * v7) = v8 == v9;
            break;
          case 0x13:
            *(*(a1 + 0x20) + 4 * v7) = v8 | v9;
            break;
          case 0x14:
            *(*(a1 + 0x20) + 4 * v7) = v8 & v9;
            break;
          case 0x15:
            *(*(a1 + 0x20) + 4 * v7) = v8 + v9;
            break;
          case 0x16:
            *(*(a1 + 0x20) + 4 * v7) = v8 - v9;
            break;
          case 0x17:
            *(*(a1 + 0x20) + 4 * v7) = v8 * v9;
            break;
          case 0x18:
            *(*(a1 + 0x20) + 4 * v7) = v8 / v9;
            break;
          case 0x19:
            *(*(a1 + 0x20) + 4 * v7) = v8 % v9;
            break;
          case 0x3A:
            *(*(a1 + 0x20) + 4 * v7) = v8 ^ v9;
            break;
          case 0x3B:
            *(*(a1 + 0x20) + 4 * v7) = v8 << v9;
            break;
          case 0x3C:
            *(*(a1 + 0x20) + 4 * v7) = v8 >> v9;
            break;
          default:
            continue;
        }
        continue;
      case 0x12u:
        *(a1 + 8) += 0x12;
        v10 = *(v4 + 3);
        v32 = 0;
        switch ( v10 )
        {
          case 0x102:
            v3 = (*(a1 + 0x38) + 4 * *(v4 + 2));
            break;
          case 0x103:
            v3 = (*(a1 + 0x40) + 4 * *(v4 + 2));
            break;
          case 0x104:
            v3 = (*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 2)));
            break;
          case 0x105:
            v3 = (*(a1 + 0x20) + 4 * *(v4 + 2));
            break;
          case 0x106:
            v32 = *(*(a1 + 0x48) + 4 * *(v4 + 2));
            break;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
        switch ( *(v4 + 6) )
        {
          case 0x100:
          case 0x101:
            v11 = *(v4 + 0xE);
            break;
          case 0x102:
            v11 = *(*(a1 + 0x38) + 4 * *(v4 + 0xE));
            break;
          case 0x103:
            v11 = *(*(a1 + 0x40) + 4 * *(v4 + 0xE));
            break;
          case 0x104:
            v11 = *(*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 0xE)));
            break;
          case 0x105:
            v11 = *(*(a1 + 0x20) + 4 * *(v4 + 0xE));
            break;
          case 0x106:
            v11 = floor(**(*(a1 + 0x48) + 4 * *(v4 + 0xE)));
            break;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
        if ( v10 == 0x106 )
        {
          v12 = v11;
          *v32 = v12;
LABEL_77:
          *(*(a1 + 0x20) + 4 * *(v4 + 2)) = floor(v12);
        }
        else
        {
          *v3 = v11;
          *(*(a1 + 0x20) + 4 * *(v4 + 2)) = v11;
        }
        continue;
      case 0x1Au:
        *(a1 + 8) += 0xC;
        switch ( *(v4 + 3) )
        {
          case 0x100:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -*(v4 + 2);
            continue;
          case 0x102:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -*(*(a1 + 0x38) + 4 * *(v4 + 2));
            continue;
          case 0x103:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -*(*(a1 + 0x40) + 4 * *(v4 + 2));
            continue;
          case 0x104:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -*(*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 2)));
            continue;
          case 0x105:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -*(*(a1 + 0x20) + 4 * *(v4 + 2));
            continue;
          case 0x106:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = -floor(**(*(a1 + 0x48) + 4 * *(v4 + 2)));
            continue;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
      case 0x1Bu:
      case 0x1Cu:
        *(a1 + 8) += 0xC;
        switch ( *(v4 + 3) )
        {
          case 0x102:
            v13 = *(a1 + 0x38);
            goto LABEL_74;
          case 0x103:
            v14 = (*(a1 + 0x40) + 4 * *(v4 + 2));
            goto LABEL_75;
          case 0x104:
            v14 = (*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 2)));
            goto LABEL_75;
          case 0x105:
            v13 = *(a1 + 0x20);
LABEL_74:
            v14 = (v13 + 4 * *(v4 + 2));
LABEL_75:
            *v14 += 2 * (*v4 == 0x1B) - 1;
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = *v14;
            continue;
          case 0x106:
            v15 = *(*(a1 + 0x48) + 4 * *(v4 + 2));
            *v15 = (2 * (*v4 == 0x1B) - 1) + *v15;
            v12 = *v15;
            goto LABEL_77;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
      case 0x1Du:
        v24 = 0;
        BSXScript::BeginDialogue();
        v25 = v4[1];
        if ( v25 >= 2u )
          v24 = 4 * *(v4 + 0xA);
        *(a1 + 8) += v24 + 4 * v25 + 6;
        return 0x1D;
      case 0x1Eu:
        ++*(a1 + 8);
        return 0x1E;
      case 0x1Fu:
        ++*(a1 + 8);
        return 0x1F;
      case 0x20u:
        ++*(a1 + 8);
        return 0x20;
      case 0x21u:
        ++*(a1 + 8);
        return 0x21;
      case 0x22u:
        ++*(a1 + 8);
        return 0x22;
      case 0x23u:
        ++*(a1 + 8);
        return 0x23;
      case 0x24u:
        ++*(a1 + 8);
        return 0x24;
      case 0x25u:
        ++*(a1 + 8);
        return 0x25;
      case 0x26u:
        ++*(a1 + 8);
        return 0x26;
      case 0x27u:
        ++*(a1 + 8);
        return 0x27;
      case 0x28u:
        ++*(a1 + 8);
        return 0x28;
      case 0x29u:
        ++*(a1 + 8);
        return 0x29;
      case 0x2Au:
        ++*(a1 + 8);
        return 0x2A;
      case 0x2Bu:
        ++*(a1 + 8);
        return 0x2B;
      case 0x2Cu:
        ++*(a1 + 8);
        return 0x2C;
      case 0x2Du:
        ++*(a1 + 8);
        return 0x2D;
      case 0x2Eu:
        ++*(a1 + 8);
        return 0x2E;
      case 0x2Fu:
        ++*(a1 + 8);
        return 0x2F;
      case 0x30u:
        ++*(a1 + 8);
        return 0x30;
      case 0x31u:
        ++*(a1 + 8);
        return 0x31;
      case 0x32u:
        ++*(a1 + 8);
        return 0x32;
      case 0x33u:
        v33[0] = 0xFFFF;
        v16 = *v5;
        v17 = *(a1 + 0xC);
        v33[1] = 0xFFFF;
        v18 = *(a1 + 0x18);
        v19 = *(v18 + 4 * v17 + 4);
        v20 = *(v18 + 4 * v17 + 8);
        v21 = *(v4 + 5);
        v34 = v16;
        v22 = *(v4 + 9);
        v35 = v19;
        v36 = v20;
        ArgList = v21;
        ArgList_4 = v22;
        if ( v19 != 0xFFFFFFFE )
        {
          if ( v19 == 0xFFFFFFFF )
          {
            ArgList = v20;
            v36 = 0;
          }
          else if ( v19 >= 0 )
          {
            ArgList = *(*(a1 + 0x60) + 8 * v21);
          }
        }
        if ( (*(a1 + 0x1A4) - *(a1 + 0x1A0)) / 0x18 )
        {
          if ( *(a1 + 0x1A0) > *(a1 + 0x1A4) )
            _invalid_parameter_noinfo();
          if ( v19 != *(sub_44C040() + 8) )
          {
            X = ArgList;
            sub_49B4E0(ArgList_4);
            sub_49B220(1, L"CScript::Fetch : 登録されている選択肢と種類が異なります : [%d]%d\n", X);
          }
        }
        BSXScript::RegisterChoice(v33);
        *(a1 + 8) += 0xD;
        continue;
      case 0x34u:
        v26 = *(v4 + 1);
        *(a1 + 8) += 5;
        *(a1 + 0x1AC) = v26;
        return 0x34;
      case 0x35u:
        ++*(a1 + 8);
        return 0x35;
      case 0x36u:
        *(a1 + 8) += 5;
        return 0x36;
      case 0x37u:
        ++*(a1 + 8);
        return 0x37;
      case 0x38u:
        v27 = *(v4 + 1);
        *(a1 + 8) += 5;
        *(a1 + 0x1B0) = v27;
        if ( *(a1 + 8) - 5 == *(a1 + 0x1B4) )
        {
          *(a1 + 0x1B4) = 0;
          *(a1 + 0x1B8) = 0;
        }
        sub_403F80();
        v28 = *(a1 + 0xC);
        sub_49B4E0(v28);
        sub_49B220(1, L"[%4d/%4d]Now Label : %s\n", v28);
        return 0x38;
      case 0x39u:
        ++*(a1 + 8);
        return 0x39;
      case 0x3Du:
        *(a1 + 8) += 0xC;
        switch ( *(v4 + 3) )
        {
          case 0x100:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~*(v4 + 2);
            continue;
          case 0x102:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~*(*(a1 + 0x38) + 4 * *(v4 + 2));
            continue;
          case 0x103:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~*(*(a1 + 0x40) + 4 * *(v4 + 2));
            continue;
          case 0x104:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~*(*(a1 + 0x18) + 4 * (*(a1 + 0xC) + *(v4 + 2)));
            continue;
          case 0x105:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~*(*(a1 + 0x20) + 4 * *(v4 + 2));
            continue;
          case 0x106:
            *(*(a1 + 0x20) + 4 * *(v4 + 2)) = ~floor(**(*(a1 + 0x48) + 4 * *(v4 + 2)));
            continue;
          default:
            return BSXScript::ReportUnknownTokenType();
        }
      case 0x3Eu:
        *(a1 + 8) += 4 * *v5 + 5;
        return 0x3E;
      case 0x3Fu:
        ++*(a1 + 8);
        return 0x3F;
      case 0x40u:
        ++*(a1 + 8);
        return 0x40;
      case 0x41u:
        ++*(a1 + 8);
        return 0x41;
      default:
        X_4 = *v4;
        sub_49B4E0(*v4);
        sub_49B340(0, L"CScript::Fetch", L"不明な命令が入力されました : %d\n", X_4);
        return 0xFFFFFFFE;
    }
  }
}