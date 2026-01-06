# abv-admin

The abvchorus.org site has existed for many years and has evolved to meet the needs of the chorus. Any admin tool changes will respect that evolution. What chorus members see today will essentially be what they see when admin tools are added.

## proposed changes

Underneath the structure that organizes the site will change. The music pages will be generated from a database. The calendar pages may be generated from another database. 

The admin tools will be divided into two basic applications. One to maintain the calendar page (cal-app),  and one to maintain the songs page (song-app)

Both the music-complete.html page and the music-current.html pages will be generated from the songs database. The songs database, while not containing the actual files, will point to where the files are stored. 

The calendar database will evolve to allow for the archiving of years and seasons, and the setlists for each concert. 

### file storage changes

File storage will change in significant ways. While the following descriptions mainly apply to songs, descriptions of changes to calendar created entries are still in design stages.

<b><i>The resources folder and subfolders will eventually be phased out.</i></b> Its current organization has files for songs scattered over multiple resource folders, which is not suitable for the song-app or database. There is no need to separate folders by file type `audio` or `print` as that diistinction can be inferred from the file extension.

A new storage location may be structured as follows:

```text
- public_html
  - assets
    - songs
      - a_song_name_folder
          sheetmusic.pdfs...
          translation.pdfs ...
          practice.mp3s...
          pronunciation.mp3s...
          chorus_recording_of song.mp3s
    - season
      - yrs 
        - 24-25
            calendar_for_year_24-25.???
        - 25-26
            calendar_for year_25-26.???  
          - fall
              a_concert_setlist.pdf...
              b_concert_setlist.pdf...
          - spring...    
    - performances
```
The folders under assets/songs/ will be adopted from the current folder names in resources/audio/. As the music-complete.html gets new or modified entries, all of the entries for that song will be upgraded, and copied to assets/songs. The files that get copied over to assets/ will be deleted from resources/. Either by attrition or a batch process, resources/ will be copied and deleted.

<b><i> Using the old site update process, you will see either links to assets/ or links to resources/. Any additions or changes you make will need to go wherever the existing links point.</i></b>

### database changes

While still in the design process, the database will be enhanced to allow for easier updating and the ability to query and group data in useful ways.

### email to margery 1/6/26

Hi Margery,

Please review this admin tools design process to date and the implications that it would have on your current methods. Please let me know if you are not OK with anything as soon as you can. I will pause working on the admin tools until you concur. To avoid having to scroll through old emails to find this in the future, this email content and any future status changes and proposed chnages will always be located in the README.md displayed here: [https://github.com/mckennatim/abv-admin](https://github.com/mckennatim/abv-admin)

