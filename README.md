## [9.1.1] Updated Version from 8.1.0 

### Fixed / Safeguards
- Firdaria: disabled for BC-era charts to prevent wrong results/crashes.

### Removed / Cleaned
- Settings → Language selector removed (non-functional); paths left commented for reference.

### UI / Usability
- Popups/windows are resizable; minor size/spacing tweaks.
- Font updates.

### Restored / Enhanced
- Arabic Parts (Settings): legacy options restored:
	- Reference other Lots as the base.
	- Use exact-degree references.
	- Added a "Modify" button for quick edits.
- Primary Directions are now show 150 years.
- Speculum: now shows "Lot of Fortune"

### Added (New Features / Modules)
- Arabic Parts: Dodecatemoria and Declination.
- Dodecatemoria: calculator popup in addition to the classic dodecatemorion table.
- Speeds: planetary speeds shown as percentages.
- Angle at Birth: new module.
- Zodiacal Releasing: new module; L2 → L3/L4 drill-down on click.
- Heliacal Rising/Setting: new module.
- Paranatellonta: new module.
- Circumambulation: new module.
- Angular Directions of Fixed Stars(Naibod Only): new module.

### Secondary Progressions
- Displays Real Date and native Age.
- Positions for Date: view planets and nodes by month/day.

### Revolutions
- Solar Revolution: ±1 Year controls and a popup showing the current return year.

### Fixed Stars
- Settings: selections can be saved without requiring “Automatic Save”.
- Updated several fixed star names.

### The settings are set to how I use them, so feel free to change anything to your liking.

--------------------------------------------------------------------------------------------------------------------------

#### 8.4.0
- Bug fixes & shows LoF position in the Speculum. To reduce ephemeris differences relative to Zet 9, reverted to the Morinus 6.0.3 ephemeris.
#### 8.4.1
- Speeds: the calculation formula has been updated
#### 8.4.2
- Heliacal Rising/Setting: this module no longer reflects the chart’s altitude (prevents inaccurate heliacal rising/setting results at higher altitudes)
#### 8.4.3 
- Rename: “Find Time and Place” → “Find Time” (the feature does not actually search locations).
- Planetary Hour: now respects the chart’s birth data and time zone.
- Rise/Set Times: now respects the chart’s birth data and time zone.
- Exact Transits: updated the notation when a retrograde planet enters a different sign & fixed an Ayanamsha bug.
- Primary Directions: fixed bugs with Antiscia and Contra-antiscia & fixed Primary Directions for the Lot of Fortune (LoF).
- Various other known bug fixes.
#### 8.4.4
- Fixed bugs in Profection chart.
#### 8.4.5
- Angular Directions of Fixed Stars: now respects the Primary Keys option
#### 8.4.6
- Paranatellonta bug fixes.
- Various other bug fixes.
#### 8.4.7
- Paranatellonta: now bolded when they share the same angle
- Monthly Profections: the 12 steps now divide the year evenly.
#### 8.4.8
- Fixed color rendering bugs.
- Solar/Lunar Revolutions: Primary directions now support "Both" (view direct & converse together).
- The Positions view of Revolution charts now includes Dodecatemoria.
#### 8.4.9
- Menus are now case-sensitive.
- Fixed a bug where the Solar Revolution chart could hide behind the natal chart
- Added a popup in Lunar Revolution chart with +1 Month / -1 Month controls.
#### 8.5.1
- Font updates.
- Angle at Birth is now bolded based on apparent magnitude and time offset: mag < 0 → ±8 min, 0 ≤ mag < 1 → ±6 min, 1 ≤ mag < 1.5 → ±5 min, mag ≥ 1.5 → ±4 min.
- Various other bug fixes.
#### 8.5.2
- Primary Directions bug fixes.
#### 8.5.3
- Rename: “Find Time” → “Find Time and Place” (the feature DOES search locations. I mistakenly renamed it earlier.).
#### 8.5.4
- Updated Swiss Ephemeris data to DE431 (2023).
- Primary Directions: Fixed an issue where switching the Node setting could shift other bodies’ direction dates.
--------------------------------------------------------------------------------------------------------------------------
### 9.0.0
- Code updates (tested and working in this environment):
	- Python: 3.7.9 (32-bit)
	- OS: Windows 10 10.0.26100
	- pip / setuptools: pip 21.3.1 / setuptools 59.8.0
	- wxPython: 4.0.7.post2 (Phoenix), wxWidgets 3.0.5 / msw
	- Pillow: 9.5.0
	- NumPy: 1.21.6
- Font update: Rolled back to the FreeSans font previously used by Morinus.
- Multilingual support: English, Hungarian, Spanish, Italian, French, Russian, Chinese (Simplified), Chinese (Traditional), and Korean supported (fonts changed for Chinese and Korean).
- UI additions: Added time and birth-time rectification controls at the top of Circumambulations and Angular Directions of Fixed Stars.
- Bug fix: Resolved an issue where PDs in Chart was not displayed.
- Bug fix (Ayanamsha & nodes interaction): Fixed planetary positions changing when node options were modified after setting the Ayanamsha.
- Speculum: Added Dodecatemoria notation.
- English mtexts (menus): Corrected inconsistent phrasings.
- Arabic Parts settings: Fixed a bug where the Active flag applied only to the first item.
#### 9.0.1
- Bugfix: solar revolution not displayed with Ayanamsha enabled.
#### 9.0.2
- Bugfix: Heliacal Risings/Setting calender bug fix.
- Triplicity option header alignment fix.
#### 9.0.3
- Primary Directions options now allow Dsc and IC to be controlled independently.
- Updated an error message that incorrectly instructed users to check a nonexistent question-mark.
#### 9.0.4
- Arabic Parts changed
    - Revamped the settings UI for Arabic Parts.
    - In Tables, formulas are now displayed using symbols.
    - Arabic Parts can now be displayed on the chart’s outer wheel.
#### 9.0.5
- Fixed a bug where planetary positions changed when Ayanamsa was enabled and the Whole Sign house system wasn’t applied.
- Improved city search reliability/performance; fixed cases where some city names couldn’t be found or took too long, and added a “Use altitude” button.
- Elections chart: now displays the chart date in the footer.
- Reduced label overlap when showing Lots (Arabic Parts) on the outer wheel.
- Fixed an issue that prevented charts from being drawn after “Restore Default.”
- Fixed incorrect values when Lots (Arabic Parts) were shown on the outer wheel with Ayanamsa enabled.
#### 9.0.6
- Reduced label overlap when showing Lots (Arabic Parts) and Fortuna on the outer wheel.
#### 9.0.7
- Fixed an issue where the Arabic Parts settings could reference a non-existent part.
- Updated: When Arabic Parts are drawn on the outer wheel, the Lot of Fortune (Fortuna) is now shown even if no other Arabic Parts are defined.
#### 9.0.8
- Fixed an issue where pressing Enter after editing a data field applied the change without showing the “Do you want to discard current horoscope?” message.
- Fixed a compatibility issue where .hor files saved in Morinus 9 could not be opened in earlier versions of Morinus.
#### 9.0.9
- Unified fonts across Transit, Secondary Progressions, and the main status bar.
- Heliacal Rising/Setting calculations once again incorporate site altitude.
- Relocated the Topocentric option within Options → Appearance.
#### 9.1.0
- Heliacal Risings/Settings algorithm revise: set scale height to the standard 8,000 m, added a refraction approximation based on pressure and temperature, changed the naked-eye limiting magnitude to 6.0.
#### 9.1.1
- Heliacal Risings/Settings: Adjusted the algorithm’s heuristic parameters.