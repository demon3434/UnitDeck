#!/usr/bin/env bash
# ==============================================================================
# UnitDeck - Debian 宿主机辅助管理与一键运维脚本
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_banner() {
    echo -e "${BLUE}"
    echo "=========================================================="
    echo "         UnitDeck - AI 服务与显存管理控制台               "
    echo "=========================================================="
    echo -e "${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[错误] 未检测到 Docker，请先安装 Docker。${NC}"
        echo "Debian 安装命令参考: curl -fsSL https://get.docker.com | bash"
        exit 1
    fi
}

start_app() {
    check_docker
    echo -e "${GREEN}[INFO] 正在构建并后台启动 UnitDeck 容器...${NC}"
    docker compose up -d --build
    echo -e "${GREEN}[成功] UnitDeck 现已成功启动！${NC}"
    echo -e "访问地址: ${YELLOW}http://$(hostname -I | awk '{print $1}'):8080${NC}"
    echo -e "默认账号: ${YELLOW}admin${NC} | 默认密码: ${YELLOW}admin123${NC}"
}

stop_app() {
    echo -e "${YELLOW}[INFO] 正在停止 UnitDeck 容器...${NC}"
    docker compose down
    echo -e "${GREEN}[成功] 容器已停止。${NC}"
}

restart_app() {
    echo -e "${YELLOW}[INFO] 正在重启 UnitDeck 容器...${NC}"
    docker compose restart
    echo -e "${GREEN}[成功] 容器已重启。${NC}"
}

view_logs() {
    echo -e "${BLUE}[INFO] 正在查看 UnitDeck 容器实时日志 (按 Ctrl+C 退出)...${NC}"
    docker compose logs -f --tail=100
}

reset_password() {
    echo -e "${YELLOW}[INFO] 正在重置 UnitDeck 管理员密码为默认 (admin123)...${NC}"
    if [ -f "./data/auth.json" ]; then
        rm -f "./data/auth.json"
        docker compose restart
        echo -e "${GREEN}[成功] 密码已重置为: admin123${NC}"
    else
        echo -e "${GREEN}[INFO] 认证文件尚未生成，默认密码即为 admin123${NC}"
    fi
}

show_status() {
    echo -e "${BLUE}[INFO] 查看容器状态:${NC}"
    docker compose ps
}

show_banner
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    logs)
        view_logs
        ;;
    status)
        show_status
        ;;
    reset-pwd)
        reset_password
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|logs|status|reset-pwd}"
        echo ""
        echo "  start      - 构建并启动 UnitDeck"
        echo "  stop       - 停止 UnitDeck"
        echo "  restart    - 重启 UnitDeck"
        echo "  logs       - 查看容器实时日志"
        echo "  status     - 查看容器运行状态"
        echo "  reset-pwd  - 重置管理员密码为默认值 (admin123)"
        echo ""
        exit 1
        ;;
esac

