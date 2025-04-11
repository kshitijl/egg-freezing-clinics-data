# Comparing egg freezing clinics: how much they do and how often they succeed

Here's a spreadsheet of the numbers: https://docs.google.com/spreadsheets/d/1jKBv5hCiNwW5xj5uuZt8c-nWPUVwOQdoIPpOOIM3Re0/edit?usp=sharing

Here's a map of the clinics: https://www.google.com/maps/d/edit?mid=1S83q4YGx8PDlHf0WsteWSHJGSUx-vMw&ll=40.738885362710654,-73.9075958112087&z=12

# What if I don't live in/near NYC?

I care about NYC area clinics so that's what's here.

If you care about some other place then use https://art.cdc.gov/artclinics to search by zipcode, then grab the json returned by the request to https://art.cdc.gov/api/ClinicListByLocation/location?zip=11217&distance=50 which you should be able to see in the Fetch/XHR requests section in dev tools.

Once you have that json, save it as `clinics-pp.json`. Run `./download-clinic-data.py`, then `./consolidate.py`, then `./to-csv.py`. I guess work hard to debug any errors that happen lol. Final results will be in `fertility_centers_data.csv`.

Or, idk, you can bother me and I'll make this nicer and auto-updating and stuff. Good luck! Now go forth and multiply.

