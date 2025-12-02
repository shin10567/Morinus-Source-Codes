## [9.5.3] Updated Version from 8.1.0 

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
- Heliacal Risings/Settings algorithm revise: Set scale height to the standard 8,000 m, added a refraction approximation based on pressure and temperature, changed the naked-eye limiting magnitude to 6.0.
#### 9.1.1
- Heliacal Risings/Settings: Adjusted the algorithm’s heuristic parameters.
#### 9.1.2
- Zodiacal Releasing bug fix
- Minor border issue solved
#### 9.1.3
- Minor Bugs fix
#### 9.1.4
- Heliacal Risings/Settings bug fix & algorithm chanegs
#### 9.1.5
- Heliacal Risings/Settings now consider the effects of moonlight & algorithm chanegs
#### 9.1.6
- Heliacal Risings/Settings calender bug fix & algorithm chanegs
#### 9.1.7
- Added Solar & Lunar Eclipses: shows all solar and lunar eclipses within ±1 year of the chart date.
- Speculum: adjusted display window size.
#### 9.1.8
- Swapped the positions of “Misc(Miscellaneous)” and “Eclipses” in the UI and exchanged their keyboard shortcuts; updated shortcut labels accordingly.
#### 9.1.9
- Timezone bug fix
#### 9.2.0
- Angular Directions of Fixed Stars bug fix
#### 9.2.1
- Angular Directions of Fixed Stars: added Age and Direct/Converse pop-up controls; angles can now be selected (Asc, Dsc, MC, IC).
#### 9.2.2
- Fix: Corrected Planetary Day and Hour calculation when using the Julian calendar (now matches the Gregorian-equivalent moment).
- Enhancement: Planetary Day/Hour glyphs are now drawn with user-defined planet colors (falls back to text color in B/W).
- Feature: Added Hour Lord column to Profections (after Asc and MC), following the Chaldean order starting from the chart’s current Hour Lord; rendered with user colors.
#### 9.2.3
- Now respects Morinus 8.1.0's shortcut keys
- Grouped and re-arraned menus
#### 9.2.4
- Positions for Date bug fix
#### 9.2.5
- Re-arraned menus
#### 9.2.6
- Chart information is now displayed inside the chart image.
#### 9.2.7
- Added Decennials. L3/L4 use the Valens method.
#### 9.2.8
- Changed the default start date for Revolution scan.
- Fixed Hour Lord and Day Lord displaying incorrectly in Revolution charts.
- Fixed Dodecatemoria when Ayanamsha is enabled.
- Fixed Antiscia when Ayanamsha is enabled.
- Fixed Revolutions when Ayanamsha is enabled.
- Reordered items in the Options menu.
- When outer-wheel overlays (Dodecatemoria, Antiscia/Contra-Antiscia, Arabic Parts, etc.) are enabled, they now also appear in Profections, Secondary Progressions, Elections, Revolutions, Transits, and Sun Transits.
#### 9.2.9
- Secondary Progressions: unified status-bar behavior.
- Options/Speculum: Dodecatemoria can be toggled on/off.
- Dodecatemoria Calculator: now inherits from CommonWnd and supports saving as an image; removed the absolute ecliptic-longitude input.
- Reorganized Options.
#### 9.3.0
- Fixed Almuten label overlap and adjusted table sizing
- Added borders and separators to the Topical Almuten settings section
- Grouped and reorganized the Options menu
#### 9.3.1
- Right-aligned the Planetary Day/Hour, House System, and Ayanamsha labels.
#### 9.3.2
- Enabled saving on Decennials L3/L4.
- Fixed an issue where planetary glyph colors did not update in Black & White mode for Heliacal Risings/Settings and Paranatellonta.
- Dodecatemoria: moved the “Dodecatemoria Calculator” context-menu item above “Save as Bitmap”; clicking it now opens the calculator.
#### 9.3.3
- Partially restored the Help (?) button in the top-right corner.
#### 9.3.4
- Zodiacal Releasing bug fixes
- Adjusted the Angles at Birth input parameter to a maximum of 12 minutes
- Added “?” help to Angles at Birth parameters, Arabic Parts Options, and the Dodecatemoria Calculator
#### 9.3.5
- Arabic Parts Options bug fix
#### 9.3.6
- Arabic Parts bug fix
#### 9.3.7
- Arabic Parts & Fortuna interaction bug fix
#### 9.3.8
- Decennials: show start-selection popup on first open
- Heliacal Risings/Settings: display Atmospheric Extinction
- Fixed Stars’ Aspects & Aspects: fixed label overlap
#### 9.3.9
- Arabic Parts bug fix
#### 9.4.0
- Updated the fixed-star catalog data to the latest sefstars.txt.
- Stars can be displayed under the alias the user selects.
- If a star has no traditional name, selecting it automatically sets its “Nomencl.” entry as the alias.
- Reduced label overlap for closely spaced fixed stars.
#### 9.4.1
- Angles at Birth parameter: narrowed the input field width; set the valid input range to 1–31.
- Circumambulations: fixed a bug where the starting age was negative when using the Julian calendar; replaced the minute/second symbols with those used in the Speculum.
- Status bar (Main Chart, Revolution, Profection, Election, Transit, Sun Transit): replaced “:” with “°” in the latitude/longitude display.
- Zodiacal Releasing: fixed an issue where chart times near midnight incorrectly used the previous day as the start date.
#### 9.4.2
- Raised the limit of the Firdaria and Profections tables to 150 years.
#### 9.4.3
- Mundane Fortuna now respects the chart’s day/night status and the Fortuna formula selected under Options → Planets/Points → Arabic Parts.
- Primary Directions updated to use Mundane Fortuna.
#### 9.4.4
- Patched Positions for Date to start at the same time as the main chart.
- Added help texts to Positions for Date, reordered fields, and refined calculation precision (Mean Time).
#### 9.4.5
- Circumambulations starting date bug fix. 
#### 9.4.6
- Paranatellonta bug fix
#### 9.4.7
- "Show Traditional Names of Fixed Stars in PD-List" bug fix
#### 9.4.8
- In fact, Placidus did not change the formula for the Mundane Fortuna according to day and night, and always used the Moon’s declination. Therefore, it is not appropriate for the Mundane Fortuna formula to vary by day/night, and the previous update that introduced such a change has been reverted.
#### 9.4.9
- Added "Fixed Star Parallels": Shows declination parallels with fixed stars within 15 arc minutes before and after.
#### 9.5.0
- Paranatellonta bug fix
#### 9.5.1
- Paranatellonta bug fix
#### 9.5.2
- Changed the method for computing apparent magnitudes of fixed stars (now using swe_fixstar_mag).
#### 9.5.3
- Total, annular, and hybrid solar eclipses and total lunar eclipses that are closest before and after the chart time are now shown in bold.

--------------------------------------------------------------------------------------------------------------------------

#### I’m not a developer by trade; I was simply a Morinus user who felt inconveniences while using the program.

#### I addressed a few of those personal inconveniences and added features I needed. As I have no programming background, most of the code was generated with the help of AI tools.

### Known issues
- Error when applying ayanamsa in Circumambulations
- Error when applying ayanamsa in Revolutions
- Error when applying ayanamsa in the Arabic Parts (degree reference) feature