# -*- coding: utf-8 -*-
import astrology
import houses
import planets
import fortune
import chart
import mtexts
import util
import math

class ArabicParts:
    '''Computes Arabic Parts'''

    NAME = 0
    FORMULA = 1
    DIURNAL = 2
    LONG = 3
    DEGWINNER = 4

    REFASC = 0
    REFHC2 = REFASC+1
    REFHC3 = REFHC2+1
    REFIC = REFHC3+1
    REFHC5 = REFIC+1
    REFHC6 = REFHC5+1
    REFDESC = REFHC6+1
    REFHC8 = REFDESC+1
    REFHC9 = REFHC8+1
    REFMC = REFHC9+1
    REFHC11 = REFMC+1
    REFHC12 = REFHC11+1

    ASC = 0
    HC2 = ASC+1
    HC3 = HC2+1
    IC = HC3+1
    HC5 = IC+1
    HC6 = HC5+1
    DESC = HC6+1
    HC8 = DESC+1
    HC9 = HC8+1
    MC = HC9+1
    HC11 = MC+1
    HC12 = HC11+1
    PLOFFS = HC12+1
    SUN = PLOFFS
    MOON = SUN+1
    MERCURY = MOON+1
    VENUS = MERCURY+1
    MARS = VENUS+1
    JUPITER = MARS+1
    SATURN = JUPITER+1
    LORDOFFS = SATURN+1
    ASCLORD = LORDOFFS
    HC2LORD = ASCLORD+1
    HC3LORD = HC2LORD+1
    ICLORD = HC3LORD+1
    HC5LORD = ICLORD+1
    HC6LORD = HC5LORD+1
    DESCLORD = HC6LORD+1
    HC8LORD = DESCLORD+1
    HC9LORD = HC8LORD+1
    MCLORD = HC9LORD+1
    HC11LORD = MCLORD+1
    HC12LORD = HC11LORD+1
    SPECIAL = HC12LORD+1
    LOF = SPECIAL
    LOFLORD = LOF+1
    SYZ = LOFLORD+1
    SYZLORD = SYZ+1
    DEG = SYZLORD+1
    DEGLORD = DEG+1
    RE = DEGLORD+1
    REFLORD = RE+1

    HNUM = houses.Houses.HOUSE_NUM-1

    def _get_refordeg_triplet(self, ar_item):
        # ar_item가 (name, (A,B,C), diur, (rA,rB,rC)) 형태면 마지막을, 아니면 (0,0,0)
        try:
            trip = ar_item[3]
            if isinstance(trip, (list, tuple)) and len(trip) == 3:
                return trip
        except Exception:
            pass
        return (0,0,0)

    def __init__(self, ar, ascmc, pls, hs, cusps, fort, syz, opts): #ar is from options
        if ar == None:
            self.parts = None
        else:
            self.doms = [4, 3, 2, 1, 0, 2, 3, 4, 5, 6, 6, 5]
            self.exals = [0, 1, -1, 5, -1, -1, 6, -1, -1, 4, -1, 3]
            self.tripls = [0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2]

            asc = hs.ascmc[houses.Houses.ASC]
            desc = util.normalize(hs.ascmc[houses.Houses.ASC]+180.0)
            mc = hs.ascmc[houses.Houses.MC]
            ic = util.normalize(hs.ascmc[houses.Houses.MC]+180.0)

            cps = (asc, cusps[2], cusps[3], ic, cusps[5], cusps[6], desc, cusps[8], cusps[9], mc, cusps[11], cusps[12])
            # --- FORWARD RE SUPPORT: enable forward references (R{future}) ---
            # 활성(표시)되는 항목들의 원본 인덱스 목록을 만든다.
            enabled_idx = []
            for ii in range(len(ar)):
                try:
                    if len(ar[ii]) > 4 and not bool(ar[ii][4]):
                        continue
                except:
                    pass
                enabled_idx.append(ii)

            def _lof_lon():
                idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                asclon = cps[idAsc]
                return self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)

            # k: 표시 리스트(LoF 제외)에서 0-based 인덱스
            def _calc_lon_by_k(k, visiting):
                # 범위 밖이면 LoF로 폴백
                if k < 0 or k >= len(ar):
                    return _lof_lon()
                # 순환 참조 감지 → LoF 폴백
                if k in visiting:
                    return _lof_lon()

                ii = k
                # === 아래는 기존 본문과 동일한 계산을 요약 재구성 (A/B/C 만들기) ===
                A_id, B_id, C_id = ar[ii][ArabicParts.FORMULA]
                # 공통: RE/REFLORD 참조를 lon으로 바꿔 주는 헬퍼
                def _re_resolve(idX, ref_value):
                    ref = int(ref_value)
                    if ref == 0:
                        lonX = _lof_lon()
                    else:
                        # R1 → k=0
                        lonX = _calc_lon_by_k(ref-1, visiting | {k})
                    if idX in (ArabicParts.REFLORD,):
                        sign = int(lonX/chart.Chart.SIGN_DEG)
                        lord = -1
                        for pid in range(astrology.SE_SATURN+1):
                            if opts.dignities[pid][0][sign]:
                                lord = pid
                        if lord != -1:
                            lonX = pls.planets[lord].data[planets.Planet.LONG]
                        else:
                            # 유효 군주 없으면 LoF로 폴백
                            lonX = _lof_lon()
                    return lonX

                # --- A ---
                lonA = 0.0
                if A_id < ArabicParts.PLOFFS:
                    A_id2 = self.adjustAscendant(A_id, opts)
                    lonA = cps[A_id2]
                elif A_id < ArabicParts.LORDOFFS:
                    lonA = pls.planets[A_id-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif A_id < ArabicParts.SPECIAL:
                    A_id2 = self.adjustAscendant(A_id-ArabicParts.LORDOFFS, opts)
                    lonTmp = cps[A_id2]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    if lord != -1:
                        lonA = pls.planets[lord].data[planets.Planet.LONG]
                    else:
                        lonA = _lof_lon()
                else:
                    if A_id < ArabicParts.SYZ:
                        lonA = _lof_lon()
                        if A_id == ArabicParts.LOFLORD:
                            sign = int(lonA/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonA = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif A_id <= ArabicParts.SYZLORD:
                        lonA = syz.lon
                        if A_id == ArabicParts.SYZLORD:
                            sign = int(lonA/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonA = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif A_id < ArabicParts.RE:
                        # DEG / DEGLORD
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        val = float((refA, refB, refC)[0]) % 360.0
                        if A_id == ArabicParts.DEGLORD:
                            sign = int(val/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonA = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                        else:
                            lonA = val
                    else:
                        # RE / REFLORD
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        lonA = _re_resolve(A_id, (refA, refB, refC)[0])

                # --- B ---
                lonB = 0.0
                if B_id < ArabicParts.PLOFFS:
                    B_id2 = self.adjustAscendant(B_id, opts)
                    lonB = cps[B_id2]
                elif B_id < ArabicParts.LORDOFFS:
                    lonB = pls.planets[B_id-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif B_id < ArabicParts.SPECIAL:
                    B_id2 = self.adjustAscendant(B_id-ArabicParts.LORDOFFS, opts)
                    lonTmp = cps[B_id2]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    lonB = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                else:
                    if B_id < ArabicParts.SYZ:
                        lonB = _lof_lon()
                        if B_id == ArabicParts.LOFLORD:
                            sign = int(lonB/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonB = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif B_id <= ArabicParts.SYZLORD:
                        lonB = syz.lon
                        if B_id == ArabicParts.SYZLORD:
                            sign = int(lonB/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonB = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif B_id < ArabicParts.RE:
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        val = float((refA, refB, refC)[1]) % 360.0
                        if B_id == ArabicParts.DEGLORD:
                            sign = int(val/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonB = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                        else:
                            lonB = val
                    else:
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        lonB = _re_resolve(B_id, (refA, refB, refC)[1])

                # --- C ---
                lonC = 0.0
                if C_id < ArabicParts.PLOFFS:
                    C_id2 = self.adjustAscendant(C_id, opts)
                    lonC = cps[C_id2]
                elif C_id < ArabicParts.LORDOFFS:
                    lonC = pls.planets[C_id-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif C_id < ArabicParts.SPECIAL:
                    C_id2 = self.adjustAscendant(C_id-ArabicParts.LORDOFFS, opts)
                    lonTmp = cps[C_id2]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    lonC = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                else:
                    if C_id < ArabicParts.SYZ:
                        lonC = _lof_lon()
                        if C_id == ArabicParts.LOFLORD:
                            sign = int(lonC/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonC = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif C_id <= ArabicParts.SYZLORD:
                        lonC = syz.lon
                        if C_id == ArabicParts.SYZLORD:
                            sign = int(lonC/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonC = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                    elif C_id < ArabicParts.RE:
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        val = float((refA, refB, refC)[2]) % 360.0
                        if C_id == ArabicParts.DEGLORD:
                            sign = int(val/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            lonC = pls.planets[lord].data[planets.Planet.LONG] if lord != -1 else _lof_lon()
                        else:
                            lonC = val
                    else:
                        refA, refB, refC = self._get_refordeg_triplet(ar[ii])
                        lonC = _re_resolve(C_id, (refA, refB, refC)[2])

                # 밤차트면 B/C 스왑
                if ar[ii][ArabicParts.DIURNAL] and (not fort.abovehorizon):
                    lonB, lonC = lonC, lonB

                diff = lonB - lonC
                if diff < 0.0:
                    diff += 360.0
                lon = lonA + diff
                if lon > 360.0:
                    lon -= 360.0
                return lon
            # --- /FORWARD RE SUPPORT ---

            self.parts = []
            num = len(ar)
            for i in range(num):
                try:
                    if len(ar[i]) > 4 and not bool(ar[i][4]):
                        continue
                except:
                    pass
                part = [ar[i][ArabicParts.NAME], (ar[i][ArabicParts.FORMULA][0], ar[i][ArabicParts.FORMULA][1], ar[i][ArabicParts.FORMULA][2]), ar[i][ArabicParts.DIURNAL], 0.0, [[-1,0],[-1,0],[-1,0]]]
                #calc longitude
                #A
                idA = part[ArabicParts.FORMULA][0]
                lonA = 0.0
                if idA < ArabicParts.PLOFFS:
                    idA = self.adjustAscendant(idA, opts)
                    lonA = cps[idA]
                elif idA < ArabicParts.LORDOFFS:
                    lonA = pls.planets[idA-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif idA < ArabicParts.SPECIAL:
                    idA -= ArabicParts.LORDOFFS
                    idA = self.adjustAscendant(idA, opts)
                    lonTmp = cps[idA]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    if lord != -1:
                        lonA = pls.planets[lord].data[planets.Planet.LONG]
                    else:
                        continue
                else:
                    if idA < ArabicParts.SYZ:
                        idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                        asclon = cps[idAsc]
                        lonA = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                        if idA == ArabicParts.LOFLORD:
                            sign = int(lonA/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonA = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idA <= ArabicParts.SYZLORD:
                        lonA = syz.lon
                        if idA == ArabicParts.SYZLORD:
                            sign = int(lonA/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonA = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idA < ArabicParts.RE:
                        # DEG / DEGLORD
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = (refA, refB, refC)[0]
                        lonA = float(ref) % 360.0
                        if idA == ArabicParts.DEGLORD:
                            sign = int(lonA/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonA = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    else:
                        # RE / REFLORD  ── R0 = LoF, R1..RN = 기존 parts[0..N-1]
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = int((refA, refB, refC)[0])
                        if ref == 0:
                            # R0: LoF
                            idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                            asclon = cps[idAsc]
                            lonA = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                            if idA == ArabicParts.REFLORD:
                                sign = int(lonA/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonA = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    continue
                        else:
                            ref -= 1  # R1→parts[0]
                            # FORWARD RE: 앞/뒤 모두 허용, 순환 시 LoF 폴백
                            lonA = _calc_lon_by_k(ref, {i})
                            if idA == ArabicParts.REFLORD:
                                sign = int(lonA/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonA = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    lonA = _lof_lon()

                #B
                idB = part[ArabicParts.FORMULA][1]
                lonB = 0.0
                if idB < ArabicParts.PLOFFS:
                    idB = self.adjustAscendant(idB, opts)
                    lonB = cps[idB]
                elif idB < ArabicParts.LORDOFFS:
                    lonB = pls.planets[idB-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif idB < ArabicParts.SPECIAL:
                    idB -= ArabicParts.LORDOFFS
                    idB = self.adjustAscendant(idB, opts)
                    lonTmp = cps[idB]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    if lord != -1:
                        lonB = pls.planets[lord].data[planets.Planet.LONG]
                    else:
                        continue
                else:
                    if idB < ArabicParts.SYZ:
                        idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                        asclon = cps[idAsc]
                        lonB = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                        if idB == ArabicParts.LOFLORD:
                            sign = int(lonB/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonB = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idB <= ArabicParts.SYZLORD:
                        lonB = syz.lon
                        if idB == ArabicParts.SYZLORD:
                            sign = int(lonB/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonB = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idB < ArabicParts.RE:
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = (refA, refB, refC)[1]
                        lonB = float(ref) % 360.0
                        if idB == ArabicParts.DEGLORD:
                            sign = int(lonB/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonB = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    else:
                        # RE / REFLORD  ── R0 = LoF, R1..RN
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = int((refA, refB, refC)[1])
                        if ref == 0:
                            idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                            asclon = cps[idAsc]
                            lonB = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                            if idB == ArabicParts.REFLORD:
                                sign = int(lonB/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonB = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    continue
                        else:
                            ref -= 1  # R1→parts[0]
                            lonB = _calc_lon_by_k(ref, {i})
                            if idB == ArabicParts.REFLORD:
                                sign = int(lonB/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonB = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    lonB = _lof_lon()

                #C
                idC = part[ArabicParts.FORMULA][2]
                lonC = 0.0
                if idC < ArabicParts.PLOFFS:
                    idC = self.adjustAscendant(idC, opts)
                    lonC = cps[idC]
                elif idC < ArabicParts.LORDOFFS:
                    lonC = pls.planets[idC-ArabicParts.PLOFFS].data[planets.Planet.LONG]
                elif idC < ArabicParts.SPECIAL:
                    idC -= ArabicParts.LORDOFFS
                    idC = self.adjustAscendant(idC, opts)
                    lonTmp = cps[idC]
                    sign = int(lonTmp/chart.Chart.SIGN_DEG)
                    lord = -1
                    for pid in range(astrology.SE_SATURN+1):
                        if opts.dignities[pid][0][sign]:
                            lord = pid
                    if lord != -1:
                        lonC = pls.planets[lord].data[planets.Planet.LONG]
                    else:
                        continue
                else:
                    if idC < ArabicParts.SYZ:
                        idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                        asclon = cps[idAsc]
                        lonC = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                        if idC == ArabicParts.LOFLORD:
                            sign = int(lonC/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonC = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idC <= ArabicParts.SYZLORD:
                        lonC = syz.lon
                        if idC == ArabicParts.SYZLORD:
                            sign = int(lonC/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonC = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    elif idC < ArabicParts.RE:
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = (refA, refB, refC)[2]
                        lonC = float(ref) % 360.0
                        if idC == ArabicParts.DEGLORD:
                            sign = int(lonC/chart.Chart.SIGN_DEG)
                            lord = -1
                            for pid in range(astrology.SE_SATURN+1):
                                if opts.dignities[pid][0][sign]:
                                    lord = pid
                            if lord != -1:
                                lonC = pls.planets[lord].data[planets.Planet.LONG]
                            else:
                                continue
                    else:
                        # RE / REFLORD  ── R0 = LoF, R1..RN
                        refA, refB, refC = self._get_refordeg_triplet(ar[i])
                        ref = int((refA, refB, refC)[2])
                        if ref == 0:
                            idAsc = self.adjustAscendant(ArabicParts.ASC, opts)
                            asclon = cps[idAsc]
                            lonC = self.getLoFLon(opts.lotoffortune, asclon, pls, fort.abovehorizon)
                            if idC == ArabicParts.REFLORD:
                                sign = int(lonC/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonC = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    continue
                        else:
                            ref -= 1  # R1→parts[0]
                            lonC = _calc_lon_by_k(ref, {i})
                            if idC == ArabicParts.REFLORD:
                                sign = int(lonC/chart.Chart.SIGN_DEG)
                                lord = -1
                                for pid in range(astrology.SE_SATURN+1):
                                    if opts.dignities[pid][0][sign]:
                                        lord = pid
                                if lord != -1:
                                    lonC = pls.planets[lord].data[planets.Planet.LONG]
                                else:
                                    lonC = _lof_lon()
 
                # Diurnal 스위치: 밤차트(태양 지평선 아래)에서는 B와 C를 바꿔 A + C - B로
                if part[ArabicParts.DIURNAL] and (not fort.abovehorizon):
                    tmp = lonB
                    lonB = lonC
                    lonC = tmp

                diff = lonB-lonC
                if diff < 0.0:
                    diff += 360.0
                lon = lonA+diff
                if lon > 360.0:
                    lon -= 360.0

                part[ArabicParts.LONG] = lon

                tmplon = lon
                degwinner = [[-1,0],[-1,0],[-1,0]]
                for p in range(astrology.SE_SATURN+1):
                    score = 0
                    scoretxt = ''
                    if opts.ayanamsha != 0:
                        tmplon = util.normalize(tmplon-opts.ayanamsha)

                    s, st, sh = self.getData(opts, p, tmplon, fort.abovehorizon)
                    score += s
                    scoretxt += st

                    if score > degwinner[0][1]:
                        degwinner[0][0] = p
                        degwinner[0][1] = score
                        degwinner[1][0] = -1
                        degwinner[2][0] = -1
                    elif score == degwinner[0][1]:
                        if degwinner[1][0] == -1:
                            degwinner[1][0] = p
                        else:
                            degwinner[2][0] = p


                part[ArabicParts.DEGWINNER] = degwinner

                self.parts.append(part)


    def adjustAscendant(self, Id, opts):
        if opts.arabicpartsref != 0:
            Id += opts.arabicpartsref
            if Id > ArabicParts.HNUM:
                Id -= ArabicParts.HNUM

        return Id


    def getLoFLon(self, typ, asclon, pls, abovehorizon):
        lon = 0.0
        if typ == chart.Chart.LFMOONSUN:
            diff = pls.planets[astrology.SE_MOON].data[planets.Planet.LONG]-pls.planets[astrology.SE_SUN].data[planets.Planet.LONG]
            if diff < 0.0:
                diff += 360.0
            lon = asclon+diff
            if lon > 360.0:
                lon -= 360.0
        elif typ == chart.Chart.LFDSUNMOON:
            diff = 0.0
            if abovehorizon:
                diff = pls.planets[astrology.SE_SUN].data[planets.Planet.LONG]-pls.planets[astrology.SE_MOON].data[planets.Planet.LONG]
            else:
                diff = pls.planets[astrology.SE_MOON].data[planets.Planet.LONG]-pls.planets[astrology.SE_SUN].data[planets.Planet.LONG]

            if diff < 0.0:
                diff += 360.0
            lon = asclon+diff
            if lon > 360.0:
                lon -= 360.0
        elif typ == chart.Chart.LFDMOONSUN:
            diff = 0.0
            if abovehorizon:
                diff = pls.planets[astrology.SE_MOON].data[planets.Planet.LONG]-pls.planets[astrology.SE_SUN].data[planets.Planet.LONG]
            else:
                diff = pls.planets[astrology.SE_SUN].data[planets.Planet.LONG]-pls.planets[astrology.SE_MOON].data[planets.Planet.LONG]

            if diff < 0.0:
                diff += 360.0
            lon = asclon+diff
            if lon > 360.0:
                lon -= 360.0

        return lon


    def getData(self, opts, i, lon, daytime):
        '''i is the index of the planet, and lon is the longitude to check'''

        score = 0
        scoretxt = ''
        share = 0

        sign = int(lon/chart.Chart.SIGN_DEG)
        if i == self.doms[sign]:
            sc = opts.dignityscores[0]
            score += sc
            add = '+'
            if scoretxt == '':
                add = ''
            scoretxt += add+str(sc)
            share += 1
        if self.exals[sign] != -1 and i == self.exals[sign]:
            sc = opts.dignityscores[1]
            score += sc
            add = '+'
            if scoretxt == '':
                add = ''
            scoretxt += add+str(sc)
            share += 1
        if opts.oneruler:
            tr = self.tripls[sign]
            tripl = 0
            if daytime:
                tripl = opts.trips[opts.seltrip][tr][0]
            else:
                tripl = opts.trips[opts.seltrip][tr][1]

            if tripl == i:
                sc = opts.dignityscores[2]
                score += sc
                add = '+'
                if scoretxt == '':
                    add = ''
                scoretxt += add+str(sc)
                share += 1
        else:
            tr = self.tripls[sign]
            for k in range(3):#3 is the maximum number of triplicity rulers
                tripl = opts.trips[opts.seltrip][tr][k]

                if tripl != -1 and tripl == i:
                    sc = opts.dignityscores[2]
                    score += sc 
                    add = '+'
                    if scoretxt == '':
                        add = ''
                    scoretxt += add+str(sc)
                    share += 1
                    break

        pos = lon%chart.Chart.SIGN_DEG

        subnum = len(opts.terms[0][0])
        summa = 0.0
        for t in range(subnum):
            summa += opts.terms[opts.selterm][sign][t][1]#degs
            if summa > pos:
                break

        term = opts.terms[opts.selterm][sign][t][0]#planet
        if term == i:
            sc = opts.dignityscores[3]
            score += sc
            add = '+'
            if scoretxt == '':
                add = ''
            scoretxt += add+str(sc)
            share += 1

        dec = int(pos/10)
        decan = opts.decans[opts.seldecan][sign][dec]
        if decan == i:
            sc = opts.dignityscores[4]
            score += sc
            add = '+'
            if scoretxt == '':
                add = ''
            scoretxt += add+str(sc)
            share += 1

        return score, scoretxt, share


