import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  // we are checking if database is already created rn
  Future<Database> get database async {
    if (_database != null) return _database!; // if its not null that means we have it
    // if not we init the db file 
    _database = await _initDB('tufdiet.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 2,
      onCreate: _createDB,
      onUpgrade: _upgradeDB,
    );
  }

  Future _upgradeDB(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      try { await db.execute('ALTER TABLE profiles ADD COLUMN avatar TEXT'); } catch (_) {}
      try { await db.execute('ALTER TABLE profiles ADD COLUMN bio TEXT'); } catch (_) {}
      try { await db.execute('ALTER TABLE profiles ADD COLUMN social_link TEXT'); } catch (_) {}
    }
  }

  // --- DATABASE CREATION ---
  // this method will handle all the creating tables stuff
  Future _createDB(Database db, int version) async {
    // defining types as a constant so it will be easier later
    const idType = 'INTEGER PRIMARY KEY AUTOINCREMENT';
    const textType = 'TEXT NOT NULL';
    const textNullType = 'TEXT';
    const integerType = 'INTEGER NOT NULL';
    const doubleType = 'REAL NOT NULL';
    const doubleNullType = 'REAL';

    await db.execute('''
// profiles table is for the users body measurements and stuff
CREATE TABLE profiles (
  id $idType,
  user_id $integerType,
  username $textType,
  height $doubleNullType,
  weight $doubleNullType,
  age $integerType,
  gender $textNullType,
  activity_level $textType,
  goal $textType,
  water_target $integerType,
  water_consumed $integerType,
  avatar $textNullType,
  bio $textNullType,
  social_link $textNullType,
  target_calories $doubleNullType,
  target_protein $doubleNullType,
  target_carbs $doubleNullType,
  target_fat $doubleNullType
)
''');

    await db.execute('''
// meals table works like a back-up list for the scanned foods
CREATE TABLE meals (
  id $idType,
  server_id $integerType,
  food_name $textType,
  calories $doubleType,
  protein $doubleType,
  carbs $doubleType,
  fat $doubleType,
  ai_confidence $doubleType,
  created_at $textType
)
''');
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
