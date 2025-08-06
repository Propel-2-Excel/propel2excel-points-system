# Propel2Excel Points System

A career-focused Discord bot that motivates and rewards student achievement through a points system, real-time activity tracking, moderation tools, and interactive rewards - creating an engaging, supportive, and growth-driven online community.

## 🚀 MVP Features

### User Roles & Access
- **Admin**: Full access to all dashboards and management
- **Student**: Access to own dashboard, points tracking, and incentive redemption
- **Company**: Limited access to aggregated student data
- **University**: Limited access to student analytics

### Points System
- Resume upload: +20 pts
- Event attendance: +15 pts
- Resource share: +10 pts
- Like/interaction: +2 pts
- LinkedIn post: +5 pts
- Discord activity: +5 pts

### Incentives
- Azure Certification (50 pts)
- Hackathon Entry (100 pts)
- Resume Review (75 pts)

## 🛠️ Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens
- **Discord Integration**: discord.py
- **API Documentation**: drf-spectacular (Swagger)

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd propel2excel-points-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "SECRET_KEY=django-insecure-your-secret-key-here-change-in-production
   DEBUG=True
   DATABASE_URL=sqlite:///p2e.db" > .env
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## 🔗 API Endpoints

### Authentication
- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - Login user
- `GET /api/users/profile/` - Get current user profile

### Points System
- `POST /api/users/{id}/add_points/` - Add points for activity
- `GET /api/points-logs/` - View points history
- `GET /api/activities/` - List available activities

### Incentives
- `GET /api/incentives/` - List available incentives
- `POST /api/redemptions/redeem/` - Redeem incentive
- `GET /api/redemptions/` - View redemption history

### Admin Only
- `POST /api/redemptions/{id}/approve/` - Approve redemption
- `POST /api/redemptions/{id}/reject/` - Reject redemption

## 📚 API Documentation

Visit `/api/docs/` for interactive Swagger documentation.

## 🎮 Discord Bot Setup

1. Create a Discord application and bot
2. Get your bot token
3. Add bot token to environment variables
4. Run the Discord bot (coming soon)

## 🗄️ Database Schema

### Core Tables
- `users` - User accounts with roles and points
- `activities` - Points-earning activities
- `points_log` - History of all points earned
- `incentives` - Available rewards
- `redemptions` - Incentive redemption history
- `user_status` - User warnings and suspensions

## 🚧 Development Roadmap

### Week 1 (Current)
- ✅ Django models and API setup
- ✅ User authentication and roles
- ✅ Points system core logic
- ✅ Incentive redemption system
- 🔄 Discord bot integration
- 🔄 Frontend dashboard

### Week 2 (Future)
- Advanced analytics and reporting
- Company/university dashboards
- Real-time notifications
- Enhanced Discord integration
- Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
