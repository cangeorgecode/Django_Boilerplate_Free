from django.shortcuts import render
import random

def jesus(request):
    verse = ["Matthew 7:9-12", "Luke 6:34", "Matthew 5:13-14", "1 Corinthians 10:31", "1 Kings 17:4-16", "Phillipians 4:19", "1 Samuel 17:51", "Ephesians 4:29", "Psalm 23:5", "1 Peter 3:15", "John 6:26-40", "Galatians 5:22", "Jeremiah 29:11", "Matthew 6:22-34", "Colossians 3:23", "John 3:16", "Matthew 11:28-30", "Proverbs 18:21 ", "Proverbs 3:5-6", "Proverbs 13:12", "Proverbs 15:2", "Proverbs 15:4", "Proverbs 18:16", "Proverbs 19:6", "Matthew 25:14-30", "1 Peter 4:10", "Psalm 24:1", "Proverbs 19:21", "Isaiah 41:10", "Proverbs 14:23" ]

    random_verse = random.choice(verse)
    return render(request, 'jesus/king.html', {'random_verse': random_verse})
