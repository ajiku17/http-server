დააყენეთ შემდეგი პაკეტები:
sudo apt install python-magic

ტესტის გასაშვებად hosts ფაილში 127.0.0.1-ის გასწვრივ ჩაამატეთ example1.ge example2.ge

ტესტი ეშვება შემდეგი ბრძანებით
python run.py path/to/main.py config.json

changelog:
run.py: დაემატა ბონუსის ტესტი logTest
basichttp: დაემატა mime-typeის შემოწმება; ამოწმებს დირექტორიაში არსებულ ყველა ფაილს; გადმოწერილი ფაილის კონტეტნტი მოწმდება sha256 ჰეშით.
rangeheader: დაემატა ტესტი შემთხვევისთვის როცა range არის არასწორად გადაცემული
virtualhost: დაემატა ტესტები, აღარ არის დამოკიდებული basichttp-ზე
config.json: დაემატა ახალი vhost-ები, გასაწერი გექნებათ hosts-ს ფაილში
